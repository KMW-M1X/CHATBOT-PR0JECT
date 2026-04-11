import os
from dotenv import load_dotenv
from pymongo import MongoClient
import torch
from transformers import AutoTokenizer, AutoModel
from nlp_pipeline import analyze_user_input

# =========================
# Load Environment Variables
# =========================
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

if not MONGO_URI or not DB_NAME or not COLLECTION_NAME:
    raise ValueError("หาตัวแปรใน .env ไม่ครบเว้ย เช็คด่วน!")

# 🟢 บังคับใช้การ์ดจอ GTX 1060 ของมึง
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("กำลังเตรียมระบบค้นหาข้อมูล ร่างทอง (Qwen3 + MongoDB Atlas)...")

# =========================
# Load Embedding Model (ใช้ท่า Manual เพื่อคุม Pooling ให้เป๊ะ!)
# =========================
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-Embedding-0.6B", trust_remote_code=True)
model = AutoModel.from_pretrained("Qwen/Qwen3-Embedding-0.6B", trust_remote_code=True).to(device)

def get_embedding(text):
    inputs = tokenizer(text, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)

    # 🟢 ท่าร่างทอง (CLS Pooling + Normalize) ตรงกับที่อัปเดต DB โคตรชัวร์!
    embeddings = outputs.last_hidden_state[:, 0]
    embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
    
    return embeddings[0].cpu().tolist()

# =========================
# Connect MongoDB
# =========================
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def retrieve_data(user_text):
    """
    วิเคราะห์ข้อความผู้ใช้ + ค้นหา semantic search ใน MongoDB
    """
    # =========================
    # NLP Analysis
    # =========================
    nlp_result = analyze_user_input(user_text)

    intent = nlp_result["intent"]
    constraints = nlp_result["constraints"]
    keywords = nlp_result["keywords"]

    print("\n--- ผลการวิเคราะห์ NLP ---")
    print(f"Intent: {intent}")
    print(f"Keywords: {keywords}")
    print(f"Constraints: {constraints}")

    # =========================
    # Build Query ให้เหมือนหน้าตา DB (สำคัญมาก!)
    # =========================
    keyword_text = " ".join(keywords) if keywords else ""
    
    if intent == "Recommend_Food":
        search_query = f"เมนูอาหาร: {keyword_text}".strip()
    elif intent == "Calculate_Exercise":
        search_query = f"กิจกรรม: {keyword_text} ค่า MET".strip()
    elif intent == "Health_Advice":
        search_query = f"คำแนะนำสุขภาพ: {keyword_text}".strip()
    else:
        search_query = f"{user_text} {keyword_text}".strip()

    print(f"\n[ระบบค้นหา] Query: {search_query}")

    # =========================
    # Create Query Vector
    # =========================
    query_vector = get_embedding(search_query)

    # =========================
    # Metadata Filter (ให้ MongoDB กรองให้เลย)
    # =========================
    filter_query = {}

    if intent == "Recommend_Food":
        filter_query["type"] = "food"
        if constraints:
            filter_query["calories"] = {"$lte": constraints[0]}

    elif intent == "Calculate_Exercise":
        filter_query["type"] = "exercise"
        
    elif intent == "Health_Advice":
        filter_query["type"] = "health_advice"

    # =========================
    # MongoDB Vector Search
    # =========================
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index", # เช็คชื่อ Index ใน MongoDB มึงด้วยนะว่าชื่อนี้ป่าว
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": 50,
                "limit": 10  # 🟢 ดึงมาเผื่อไว้ 10 อันเลย ให้บอทมันเลือก
            }
        },
        {
            "$project": {
                "_id": 0,
                "name": 1,
                "type": 1,
                "calories": 1,
                "value": 1,
                "content": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]

    if filter_query:
        pipeline[0]["$vectorSearch"]["filter"] = filter_query

    print("กำลังค้นหาใน MongoDB...")
    results = list(collection.aggregate(pipeline))

    # =========================
    # Score Threshold Filter (ปรับลงมา 0.65 กำลังดี)
    # =========================
    results = [r for r in results if r.get("score", 0) >= 0.65]

    return results

# =========================
# Test
# =========================
if __name__ == "__main__":
    text = "อยากกินข้าวมันไก่ แต่ขอพลังงานไม่เกิน 500 แคลอรี"
    top_results = retrieve_data(text)

    print("\n--- ผลลัพธ์จากฐานข้อมูล ---")
    if not top_results:
        print("ไม่พบข้อมูลที่ตรงกับเงื่อนไข")
    else:
        for i, res in enumerate(top_results, 1):
            calories = res.get('calories') or res.get('value', 'N/A')
            print(f"{i}. {res['name']} | แคล/MET: {calories} | score: {res['score']:.4f}")