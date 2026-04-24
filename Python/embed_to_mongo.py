import os
import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient
import torch
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_text_splitters import RecursiveCharacterTextSplitter

# เป้าหมาย: โหลดตัวแปรสภาพแวดล้อม
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

# เป้าหมาย: เลือกระบบประมวลผลอัตโนมัติให้รองรับทุก OS (Windows, Mac, Linux)
if torch.cuda.is_available():
    device_type = "cuda"
    print("ระบบประมวลผล: CUDA")
elif torch.backends.mps.is_available():
    device_type = "mps"
    print("ระบบประมวลผล: Apple MPS")
else:
    device_type = "cpu"
    print("ระบบประมวลผล: CPU")

# เป้าหมาย: ตั้งค่าโมเดล Embedding
print("กำลังเตรียม Embedding Model...")
embeddings = HuggingFaceEmbeddings(
    model_name="intfloat/multilingual-e5-base",
    model_kwargs={'device': device_type}, # เปลี่ยนมาใช้ตัวแปรที่เช็กค่าแล้ว
    encode_kwargs={'normalize_embeddings': True}
)

def upload_to_mongo_langchain():
    # เป้าหมาย: เชื่อมต่อฐานข้อมูล
    client = MongoClient(MONGO_URI)
    collection = client[DB_NAME][COLLECTION_NAME]
    
    csv_files = [
        os.path.join("data", "thai_nutrition.csv"),
        os.path.join("data", "mets_data.csv"),
        os.path.join("data", "health_tips.csv"),
        os.path.join("data", "knowledge_base.csv")
    ]

    all_docs = []

    # เป้าหมาย: ตั้งค่าเครื่องหั่นข้อมูล (Chunking) สำหรับข้อมูล Knowledge
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200,
        add_start_index=True
    )

    for file_path in csv_files:
        if not os.path.exists(file_path):
            print(f"ข้ามไฟล์: {file_path}")
            continue

        print(f"กำลังประมวลผลไฟล์: {os.path.basename(file_path)}")
        df = pd.read_csv(file_path).fillna('')

        for _, row in df.iterrows():
            filename = os.path.basename(file_path)
            
            # เป้าหมาย: จัดเตรียมข้อมูลแยกตามประเภท
            if "thai_nutrition" in filename.lower():
                name = str(row.get('Thai_Name', '')).strip()
                if not name: continue
                content = f"passage: เมนูอาหาร: {name} ให้พลังงาน {row.get('Energy(kcal)', 0)} kcal"
                metadata = {"type": "food", "source": filename, "name": name}
                
            elif "mets_data" in filename.lower():
                name = str(row.get('activity_description_Thai', '')).strip()
                if not name: continue
                content = f"passage: กิจกรรม {name} มีค่า MET เท่ากับ {row.get('met_value', 0)}"
                metadata = {"type": "exercise", "source": filename, "name": name}
                
            elif "knowledge_base" in filename.lower() or "health_tips" in filename.lower():
                topic = str(row.get('topic', row.get('tip_name', ''))).strip()
                desc = str(row.get('description', '')).strip()
                if not topic: continue
                content = f"passage: หัวข้อ {topic}: {desc}"
                metadata = {"type": "knowledge", "source": filename, "topic": topic}
            else:
                continue

            # เป้าหมาย: สร้าง Document Object
            doc = Document(page_content=content, metadata=metadata)
            
            # เป้าหมาย: แยกหั่นข้อมูล (Split) เฉพาะบทความยาว
            if metadata["type"] == "knowledge":
                all_docs.extend(text_splitter.split_documents([doc]))
            else:
                all_docs.append(doc)

    if all_docs:
        print(f"กำลังแปลงเป็น Vector และอัปโหลด {len(all_docs)} รายการ...")
        # เป้าหมาย: บันทึกข้อมูลแบบ Vector ลงฐานข้อมูล
        MongoDBAtlasVectorSearch.from_documents(
            documents=all_docs,
            embedding=embeddings,
            collection=collection,
            index_name="vector_index"
        )
        print("อัปโหลดข้อมูลเสร็จสมบูรณ์")

if __name__ == "__main__":
    upload_to_mongo_langchain()