import os
from dotenv import load_dotenv
from pymongo import MongoClient
import torch
from transformers import AutoTokenizer, AutoModel

# โหลด env
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

# ใช้ GPU ถ้ามี
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("กำลังเตรียมโมเดล Qwen3 และเชื่อมต่อ DataBase...")

# โหลด embedding model
tokenizer = AutoTokenizer.from_pretrained(
    "Qwen/Qwen3-Embedding-0.6B",
    trust_remote_code=True
)

model = AutoModel.from_pretrained(
    "Qwen/Qwen3-Embedding-0.6B",
    trust_remote_code=True
).to(device)

# MongoDB
client = MongoClient(MONGO_URI)
collection = client[DB_NAME][COLLECTION_NAME]


def get_embedding(text):
    inputs = tokenizer(
        text,
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt"
    ).to(device)

    with torch.no_grad():
        outputs = model(**inputs)

    # 🟢 ท่าร่างทอง (CLS Pooling + Normalize) ตรงกับที่อัปเดต DB ไปเป๊ะๆ
    embeddings = outputs.last_hidden_state[:, 0]
    embeddings = torch.nn.functional.normalize(
        embeddings,
        p=2,
        dim=1
    )

    return embeddings[0].cpu().tolist()


def build_search_query(intent, keywords):
    keyword_text = " ".join(keywords) if keywords else ""

    # 🟢 เติมเครื่องหมาย ":" เข้าไปให้เหมือนหน้าตาข้อมูลใน DB แม่งจะหาแม่นขึ้น
    if intent == "Recommend_Food":
        return f"เมนูอาหาร: {keyword_text}".strip()

    elif intent == "Calculate_Exercise":
        return f"กิจกรรม: {keyword_text} ค่า MET".strip()

    elif intent == "Health_Advice":
        return f"คำแนะนำสุขภาพ: {keyword_text}".strip()

    return keyword_text if keyword_text else "ข้อมูลสุขภาพทั่วไป"


def retrieve_top_k(intent, keywords, constraints=None):
    # สร้าง query ให้ semantic ดีขึ้น
    search_query = build_search_query(intent, keywords)

    # แปลงเป็น vector
    query_vector = get_embedding(search_query)

    # 🟢 ย้าย Filter มากองตรงนี้! สั่งให้ MongoDB คัดแยกประเภทให้ตั้งแต่ตอนเสิร์ช
    filter_query = {}
    if intent == "Recommend_Food":
        filter_query["type"] = "food"
        if constraints:
            filter_query["value"] = {"$lte": constraints[0]}
    elif intent == "Calculate_Exercise":
        filter_query["type"] = "exercise"
    elif intent == "Health_Advice":
        filter_query["type"] = "health_advice"

    # vector search
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": 150,
                "limit": 10
            }
        },
        {
            "$project": {
                "_id": 0,
                "name": 1,
                "value": 1,
                "content": 1,
                "type": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]

    # 🟢 ยัด Filter ใส่ Pipeline
    if filter_query:
        pipeline[0]["$vectorSearch"]["filter"] = filter_query

    results = list(collection.aggregate(pipeline))

    # 🟢 กูเอา Filter โง่ๆ ใน Python ออกไปแล้ว (เพราะย้ายไปใส่ใน DB แทน)
    # เหลือแค่กรอง Score ขั้นต่ำ (ตั้งไว้ 0.60 กำลังสวย)
    results = [
        r for r in results
        if r.get("score", 0) > 0.60
    ]

    # rerank แบบง่ายด้วย keyword match
    if keywords:
        results.sort(
            key=lambda x: sum(
                kw.lower() in x.get("content", "").lower()
                for kw in keywords
            ),
            reverse=True
        )

    # เอา top 5
    results = results[:5]

    # fallback ถ้าไม่เจอ
    if not results:
        return [
            {
                "name": "ไม่พบข้อมูล",
                "value": None,
                "content": "ไม่พบข้อมูลที่ใกล้เคียงในฐานข้อมูล",
                "type": "fallback",
                "score": 0
            }
        ]

    return results