import os
from dotenv import load_dotenv
from pymongo import MongoClient
import torch
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch
from nlp_pipeline import analyze_user_input

# =========================
# ⚙️ 1. Setup & Device (Universal)
# =========================
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

# ระบบเลือกสมองประมวลผล (PC มึง หรือ Mac เพื่อนมึง)
if torch.cuda.is_available():
    device = "cuda"
    print("🚀 Chatbot Core: ใช้ CUDA (GTX 1060)")
elif torch.backends.mps.is_available():
    device = "mps"
    print("🍏 Chatbot Core: ใช้ Apple Silicon (MPS)")
else:
    device = "cpu"
    print("🐢 Chatbot Core: ใช้ CPU")

# =========================
# 🧠 2. Initialize LangChain E5 Embeddings
# =========================
# ต้องเป็นตัวเดียวกับที่ใช้ใน embed_to_mongo.py นะจารย์!
embeddings = HuggingFaceEmbeddings(
    model_name="intfloat/multilingual-e5-base",
    model_kwargs={'device': device},
    encode_kwargs={'normalize_embeddings': True}
)

# เชื่อมต่อ MongoDB และสร้าง Vector Store
client = MongoClient(MONGO_URI)
collection = client[DB_NAME][COLLECTION_NAME]

vector_store = MongoDBAtlasVectorSearch(
    collection=collection,
    embedding=embeddings,
    index_name="vector_index" # ชื่อ Index ใน Atlas ของมึง
)

def retrieve_data(user_text):
    """
    วิเคราะห์ข้อความผู้ใช้ + ค้นหา Semantic Search ด้วย LangChain
    """
    # 🟢 1. NLP Analysis
    nlp_result = analyze_user_input(user_text)
    intent = nlp_result["intent"]
    constraints = nlp_result["constraints"]
    keywords = nlp_result["keywords"]

    print(f"\n[NLP] Intent: {intent} | Keywords: {keywords}")

    # 🟢 2. Build Query (ต้องมี query: ตามกฎ E5)
    keyword_text = " ".join(keywords) if keywords else ""
    if intent == "Recommend_Food":
        search_query = f"query: เมนูอาหาร: {keyword_text}"
    elif intent == "Calculate_Exercise":
        search_query = f"query: กิจกรรมและการเผาผลาญ: {keyword_text}"
    else:
        search_query = f"query: {user_text} {keyword_text}"

    # 🟢 3. Metadata Filter
    pre_filter = {}
    if intent == "Recommend_Food":
        pre_filter["type"] = "food"
        if constraints:
            # ใช้คีย์ 'value' ตามที่มึงแก้ใน embed_to_mongo.py
            pre_filter["value"] = {"$lte": constraints[0]}
    elif intent == "Calculate_Exercise":
        pre_filter["type"] = "exercise"
    elif intent == "Health_Advice":
        pre_filter["type"] = "knowledge"

    # 🟢 4. LangChain Vector Search
    print(f"🔍 กำลังค้นหา: {search_query}")
    
    # ดึงข้อมูลพร้อมคะแนนความเหมือน
    docs_with_score = vector_store.similarity_search_with_score(
        query=search_query,
        k=5,
        pre_filter=pre_filter if pre_filter else None
    )

    # 🟢 5. Format Results
    results = []
    for doc, score in docs_with_score:
        if score >= 0.70: # ปรับ Threshold ตามความเหมาะสม
            results.append({
                "name": doc.metadata.get("name", "ไม่ระบุชื่อ"),
                "type": doc.metadata.get("type", "unknown"),
                "value": doc.metadata.get("value", 0), # แคลอรี หรือ MET
                "content": doc.page_content.replace("passage: ", ""),
                "score": score
            })

    return results

# =========================
# Test
# =========================
if __name__ == "__main__":
    test_text = "อยากกินข้าวมันไก่ ไม่เกิน 500 แคล"
    top_results = retrieve_data(test_text)
    
    print("\n--- ผลลัพธ์จาก LangChain + MongoDB ---")
    for i, res in enumerate(top_results, 1):
        print(f"{i}. {res['name']} | ค่า: {res['value']} | score: {res['score']:.4f}")