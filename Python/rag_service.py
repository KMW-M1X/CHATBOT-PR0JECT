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

# ระบบเลือกสมองประมวลผลอัตโนมัติ
if torch.cuda.is_available():
    device = torch.device("cuda")
    print("โหมดตัวตึง: เจอการ์ดจอกำลังรันด้วย CUDA")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
    print("โหมดลูกคุณหนู: เจอชิป Apple M-Series! กำลังรันด้วยพลัง Metal")
else:
    device = torch.device("cpu")
    print("โหมดสู้ชีวิต: ไม่เจอการ์ดจอที่รองรับ... กำลังรันด้วย CPU")

print("กำลังเตรียมโมเดล E5 และเชื่อมต่อฐานข้อมูล...")

# เอา use_safetensors=False ออก เพื่อแก้ปัญหา PyTorch v2.6+ เตะก้านคอ
tokenizer = AutoTokenizer.from_pretrained("intfloat/multilingual-e5-base")
model = AutoModel.from_pretrained("intfloat/multilingual-e5-base").to(device)

# MongoDB
client = MongoClient(MONGO_URI)
collection = client[DB_NAME][COLLECTION_NAME]

def get_embedding(text):
    # เติมคำนำหน้า query: ตามกฎของ E5
    formatted_text = f"query: {text}"
    
    inputs = tokenizer(
        formatted_text,
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt"
    ).to(device)

    with torch.no_grad():
        outputs = model(**inputs)

    # ใช้วิธี Mean Pooling ของ E5
    attention_mask = inputs['attention_mask']
    last_hidden = outputs.last_hidden_state.masked_fill(~attention_mask[..., None].bool(), 0.0)
    embeddings = last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]
    
    # ทำ Normalize
    embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

    return embeddings[0].cpu().tolist()

def build_search_query(intent, keywords):
    keyword_text = " ".join(keywords) if keywords else ""

    if intent == "Recommend_Food":
        return f"อาหาร เมนูโภชนาการ แคลอรี {keyword_text}".strip()
    elif intent == "Calculate_Exercise":
        return f"การออกกำลังกาย กิจกรรม การเผาผลาญ {keyword_text}".strip()
    elif intent == "Health_Advice":
        return f"คำแนะนำ การดูแลสุขภาพ {keyword_text}".strip()

    return keyword_text if keyword_text else "ข้อมูลสุขภาพและโภชนาการ"

def retrieve_top_k(intent, keywords, constraints=None):
    search_query = build_search_query(intent, keywords)
    query_vector = get_embedding(search_query)

    filter_query = {}
    if intent == "Recommend_Food":
        filter_query["type"] = "food"
        if constraints:
            filter_query["value"] = {"$lte": constraints[0]}
    elif intent == "Calculate_Exercise":
        filter_query["type"] = "exercise"
    elif intent == "Health_Advice":
        filter_query["type"] = "health_advice"

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

    if filter_query:
        pipeline[0]["$vectorSearch"]["filter"] = filter_query

    results = list(collection.aggregate(pipeline))

    # E5 มักจะให้คะแนนค่อนข้างสูง กรองที่ 0.75
    results = [
        r for r in results
        if r.get("score", 0) > 0.75
    ]

    if keywords:
        results.sort(
            key=lambda x: sum(
                kw.lower() in x.get("content", "").lower()
                for kw in keywords
            ),
            reverse=True
        )

    results = results[:5]

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