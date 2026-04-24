import os
from dotenv import load_dotenv
from pymongo import MongoClient
import torch
# 🟢 นำเข้า Loader ทั้ง 2 แบบมารอไว้เลย
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch

# ==========================================
# โหลดการตั้งค่าระบบและสภาพแวดล้อม
# ==========================================
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

if torch.cuda.is_available():
    device_type = "cuda"
elif torch.backends.mps.is_available():
    device_type = "mps"
else:
    device_type = "cpu"

print("กำลังเตรียมโมเดล Embedding...")
embeddings = HuggingFaceEmbeddings(
    model_name="intfloat/multilingual-e5-base",
    model_kwargs={'device': device_type},
    encode_kwargs={'normalize_embeddings': True}
)

def scrape_and_upload():
    # ==========================================
    # 🌐 สารบัญแหล่งความรู้ (รองรับทั้ง Web และ PDF)
    # ==========================================
    KNOWLEDGE_SOURCES = [
        {   "type": "web",
            "path": "https://activethai.org/article/mets-and-physical-activity-levels",
            "topic": "ความรู้เรื่อง METs จาก ActiveThai"
        },
        {   "type": "web",
            "path":"https://www.sgethai.com/article/%E0%B8%9B%E0%B8%A3%E0%B8%B0%E0%B9%82%E0%B8%A2%E0%B8%8A%E0%B8%99%E0%B9%8C%E0%B8%82%E0%B8%AD%E0%B8%87-%E0%B8%AD%E0%B8%81%E0%B9%84%E0%B8%81%E0%B9%88-%E0%B8%97%E0%B8%B5%E0%B9%88%E0%B8%AA%E0%B8%B2%E0%B8%A2/?srsltid=AfmBOoqh4RDJck_o2yet2HzbCnF3zbU7aii-rP9v6SCmWJuH4IzUHCFC",
            "topic":"ประโยชน์ของอกไก่"
        },
        {   "type": "web",
            "path": "https://www.rama.mahidol.ac.th/ramachannel/article/%E0%B8%A7%E0%B8%B4%E0%B8%98%E0%B8%B5%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B8%94%E0%B8%B7%E0%B9%88%E0%B8%A1%E0%B8%99%E0%B9%89%E0%B8%B3-%E0%B8%94%E0%B8%B5%E0%B8%95%E0%B9%88%E0%B8%AD%E0%B8%A3%E0%B9%88%E0%B8%B2/",
            "topic": "ดื่มน้ำ ยังไง ให้ดีต่อร่างกาย"
        },
        {   "type": "web",
            "path": "https://hdmall.co.th/blog/table-of-calories-in-food-types/",
            "topic": "วิธีการคํานวณแคลอรี่ ตารางปริมาณแคลอรี่ในอาหารไทย"
        },
        {
            "type": "pdf", 
            "path": "data/allergy_guide.pdf", 
            "topic": "คู่มือการจัดการอาการแพ้อาหาร"
        },
        {
            "type": "web", 
            "path": "https://smartinnovatives.com/2022/11/11/halal/", 
            "topic": "ฮาลาล Halal"
        },
        {
            "type": "web", 
            "path": "https://www.medparkhospital.com/lifestyles/how-to-lose-weight-to-be-healthy", 
            "topic": "การลดน้ำหนัก"
        },
    ]

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200,
        add_start_index=True
    )

    all_splits_to_upload = [] 

    # ==========================================
    # 🔄 วิ่งวนลูปดูดข้อมูล (ระบบสลับหัวอ่านออโต้)
    # ==========================================
    for source in KNOWLEDGE_SOURCES:
        source_type = source["type"]
        path = source["path"]
        topic = source["topic"]
        
        print(f"กำลังดำเนินการดึงข้อมูลจาก: {path} (รูปแบบ: {source_type})")
        try:
            # 🧠 ระบบสลับหัวอ่าน (Loader) อัตโนมัติ
            if source_type == "web":
                loader = WebBaseLoader(path)
            elif source_type == "pdf":
                # เช็กก่อนว่ามีไฟล์ PDF อยู่จริงไหม
                if not os.path.exists(path):
                    print(f"⚠️ ไม่พบไฟล์ PDF ที่ {path} ข้ามไปก่อนนะ!")
                    continue
                loader = PyPDFLoader(path)
            else:
                print(f"⚠️ ไม่รู้จักประเภทข้อมูล: {source_type}")
                continue

            # ดึงเนื้อหา
            documents = loader.load()
            
            # หั่นเนื้อหา
            splits = text_splitter.split_documents(documents)
            
            # ติดป้าย Metadata
            for doc in splits:
                original_text = doc.page_content.strip()
                doc.page_content = f"passage: ข้อมูลอ้างอิงเรื่อง {topic}: {original_text}"
                doc.metadata = {
                    "type": "knowledge", 
                    "source": path,
                    "topic": topic
                }
            
            all_splits_to_upload.extend(splits)
            print(f"ดำเนินการแบ่งข้อมูล '{topic}' เสร็จสิ้น (จำนวน {len(splits)} รายการ)")
            
        except Exception as e:
            print(f"❌ ไม่สามารถดึงข้อมูลจาก {path} ได้: {e}")

    # ==========================================
    # 🚀 บันทึกข้อมูลทั้งหมดลงฐานข้อมูล MongoDB Atlas
    # ==========================================
    if all_splits_to_upload:
        client = MongoClient(MONGO_URI)
        collection = client[DB_NAME][COLLECTION_NAME]

        print(f"\nกำลังแปลงข้อมูลเป็น Vector และบันทึกลงฐานข้อมูลจำนวน {len(all_splits_to_upload)} รายการ...")
        MongoDBAtlasVectorSearch.from_documents(
            documents=all_splits_to_upload,
            embedding=embeddings,
            collection=collection,
            index_name="vector_index"
        )
        print("🎉 บันทึกข้อมูลความรู้ใหม่ (ทั้ง Web และ PDF) ลงระบบเสร็จสมบูรณ์!")
    else:
        print("ไม่มีข้อมูลสำหรับบันทึกลงฐานข้อมูล กรุณาตรวจสอบ Source อีกครั้ง")

if __name__ == "__main__":
    scrape_and_upload()


