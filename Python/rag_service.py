import os
from dotenv import load_dotenv
from pymongo import MongoClient
import torch
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch

# ==========================================
# ⚙️ 1. โหลดการตั้งค่าและอุปกรณ์
# ==========================================
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")


if torch.cuda.is_available():
    device = "cuda"
    print("🚀 โหมดตัวตึง: รันด้วย CUDA ")
elif torch.backends.mps.is_available():
    device = "mps"
    print("🍏 โหมดลูกคุณหนู: รันด้วย Apple Silicon (MPS) ")
else:
    device = "cpu"
    print("🐢 โหมดสู้ชีวิต: รันด้วย CPU ")

# 🚀 ท่า LangChain: ใช้ Embeddings ตัวเดียวกับตอนสร้าง Index
embeddings = HuggingFaceEmbeddings(
    model_name="intfloat/multilingual-e5-base",
    model_kwargs={'device': device},
    encode_kwargs={'normalize_embeddings': True}
)

# เชื่อมต่อ MongoDB
client = MongoClient(MONGO_URI)
collection = client[DB_NAME][COLLECTION_NAME]

# 🧠 สร้าง Vector Store Retriever
vectorstore = MongoDBAtlasVectorSearch(
    collection=collection,
    embedding=embeddings,
    index_name="vector_index" # ต้องตรงกับชื่อใน Atlas
)

# ==========================================
# 🔍 2. ฟังก์ชันเตรียมคำถาม
# ==========================================
def build_search_query(intent, keywords):
    keyword_text = " ".join(keywords) if keywords else ""
    
    # เติมคำว่า "query:" นำหน้าเสมอตามกฎของโมเดล E5
    if intent == "Recommend_Food":
        return f"query: อาหาร เมนูโภชนาการ แคลอรี {keyword_text}".strip()
    elif intent == "Calculate_Exercise":
        return f"query: การออกกำลังกาย กิจกรรม การเผาผลาญ {keyword_text}".strip()
    elif intent == "Health_Advice":
        return f"query: คำแนะนำ การดูแลสุขภาพ {keyword_text}".strip()
    
    return f"query: {keyword_text}" if keyword_text else "query: ข้อมูลสุขภาพและโภชนาการ"

# ==========================================
# 🎯 3. ฟังก์ชันดึงข้อมูล (Retrieval)
# ==========================================
def retrieve_top_k(intent, keywords, constraints=None):
    search_query = build_search_query(intent, keywords)

    # 🛠️ ตั้งค่า Filter สำหรับ MongoDB (Metadata Filtering)
    pre_filter = {}
    if intent == "Recommend_Food":
        pre_filter["type"] = "food"
        if constraints:
            pre_filter["value"] = {"$lte": constraints[0]}
    elif intent == "Calculate_Exercise":
        pre_filter["type"] = "exercise"
    elif intent == "Health_Advice" or intent == "General_Knowledge":
        # ให้ดึงได้ทั้งคำแนะนำและข้อมูลความรู้ทั่วไป (เผื่อถามเรื่อง METs)
        pre_filter["type"] = {"$in": ["health_advice", "knowledge", "general_knowledge"]}

    # 🚀 ท่า LangChain: ค้นหาข้อมูลแบบ Similarity Search
    print(f"กำลังค้นหา: {search_query} | Filter: {pre_filter}")
    raw_results = vectorstore.similarity_search_with_score(
        query=search_query,
        k=10, # ดึงมา 10 ชิ้นก่อนเผื่อกรองทิ้ง
        pre_filter=pre_filter if pre_filter else None
    )

    results = []
    for doc, score in raw_results:
        # E5 มักจะให้คะแนนค่อนข้างสูง กรองที่ 0.75 เหมือนที่มึงทำไว้
        if score > 0.75:
            # แปลง Document Object กลับเป็น Dict เพื่อให้ app.py ไม่พัง
            results.append({
                "name": doc.metadata.get("name", doc.metadata.get("topic", "ไม่ระบุชื่อ")),
                "value": doc.metadata.get("value", 0),
                "content": doc.page_content.replace("passage: ", ""), # ตัด tag passage ออกให้ข้อความคลีนๆ
                "type": doc.metadata.get("type", "unknown"),
                "score": score
            })

    # จัดเรียงตาม Keyword (ถ้า Keyword ตรงเยอะให้อยู่บน) เหมือนโค้ดเก่ามึงเป๊ะ
    if keywords:
        results.sort(
            key=lambda x: sum(
                kw.lower() in x.get("content", "").lower()
                for kw in keywords
            ),
            reverse=True
        )

    # ตัดเอาแค่ 5 อันดับแรก
    results = results[:5]

    # ถ้าหาไม่เจอ ให้โยน Fallback กลับไป
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