# Acti-Mate: Health & Fitness AI Microservice (Python)

ระบบ Backend ประมวลผลภาษาธรรมชาติ (NLP) และระบบค้นหาข้อมูลอัจฉริยะ (RAG) สำหรับโปรเจกต์ Acti-Mate ช่วยคำนวณแคลอรี แนะนำอาหาร และวางแผนการออกกำลังกายด้วยพลังของ AI

## 🚀 เทคโนโลยีที่เลือกใช้ (Tech Stack)
- **FastAPI**: เว็บเฟรมเวิร์กความเร็วสูงสำหรับสร้าง API
- **PyTorch (CUDA)**: ประมวลผลโมเดล Deep Learning ผ่าน GPU (GTX 1060)
- **WangchanBERTa**: โมเดลภาษาไทยระดับ State-of-the-art สำหรับตัดคำและหา Entity
- **E5 Multilingual Base**: โมเดลสำหรับสร้าง Vector Embedding เพื่อค้นหาข้อมูล
- **Ollama (Qwen 2.5:7b)**: สมองส่วนการสนทนา (LLM) ที่รันในเครื่อง 100%
- **MongoDB Atlas**: ฐานข้อมูล Vector Search สำหรับจัดเก็บข้อมูลโภชนาการและค่า MET

## 📂 โครงสร้างไฟล์ในระบบ (File Descriptions)

| ไฟล์ | หน้าที่ความรับผิดชอบ |
| :--- | :--- |
| `app.py` | **Main Gateway**: รับ Request จาก Node.js, รวบรวมข้อมูลจากทุก Module และส่งให้ LLM ตอบกลับ |
| `nlp_pipeline.py` | **Thai NLP**: ใช้ WangchanBERTa วิเคราะห์ Intent (เจตนา) และ Keyword จากข้อความภาษาไทย |
| `rag_service.py` | **Vector Search**: ระบบค้นหาข้อมูล (RAG) โดยใช้โมเดล E5 และ MongoDB เพื่อดึงข้อมูลที่แม่นยำมาตอบ |
| `calculator_service.py` | **Math Engine**: รวมสูตรคำนวณ BMI, BMR, TDEE และการเผาผลาญแคลอรีตามค่า MET |
| `embed_to_mongo.py` | **Data Ingestion**: สคริปต์สำหรับนำไฟล์ CSV ในโฟลเดอร์ `/data` มาทำ Embedding และอัปโหลดลง MongoDB |
| `chatbot_core.py` | **Core Logic**: ระบบประมวลผลทางเลือกและชุดคำสั่งภายใน (จำเป็นสำหรับการทำงานร่วมกับบางส่วนของระบบ) |
| `data/` | โฟลเดอร์เก็บไฟล์ฐานข้อมูล CSV (ความรู้เรื่องอาหาร, การออกกำลังกาย, และคำแนะนำสุขภาพ) |
<br/>
# 🛠️ ขั้นตอนการติดตั้ง (Installation)

## 1. เตรียมสภาพแวดล้อม (Environment)
แนะนำให้ใช้ Python 3.10 ขึ้นไป และสร้าง Virtual Environment:
```bash
python -m venv venv #terminal
venv\Scripts\activate  # สำหรับ Windows



## 📂 โครงสร้างไฟล์ในระบบ (File Tree & Descriptions)

```text
├── data/
│   ├── health_tips.csv        # ข้อมูลคำแนะนำสุขภาพเบื้องต้น
│   ├── mets_data.csv          # ข้อมูลกิจกรรมและการเผาผลาญ (MET)
│   └── thai_nutrition.csv     # ข้อมูลโภชนาการอาหารไทย
├── app.py                     # Main Gateway: รับ Request, รวบรวมข้อมูล, และต่อกับ Ollama
├── calculator_service.py      # Math Engine: รวมสูตร BMR, BMI, TDEE, Calories Burned
├── chatbot_core.py            # Core Logic: โค้ดประมวลผลหลักและโมดูลสแตนด์บายของระบบ
├── embed_to_mongo.py          # Data Ingestion: สคริปต์ทำ Embedding จาก CSV และอัปโหลดลง MongoDB
├── nlp_pipeline.py            # Thai NLP: ตัดคำ หาคีย์เวิร์ด และจัดหมวดหมู่เจตนาของผู้ใช้
├── rag_service.py             # Vector Search: แปลงคำถามเป็น Vector 768 มิติเพื่อค้นหาใน MongoDB
├── requirements.txt           # รายชื่อ Library ที่ใช้ทั้งหมด
└── README.md                  # ไฟล์เอกสารคู่มือโปรเจกต์ (ที่คุณกำลังอ่านอยู่)
```

## 2. ติดตั้ง PyTorch สำหรับ GPU (Nvidia CUDA)
เพื่อให้การทำงานของโมเดลเร็วขึ้น ควิดตั้งเวอร์ชันที่รองรับ CUDA 12.1:

```bash
pip install torch==2.5.1+cu121 torchvision==0.20.1+cu121 torchaudio==2.5.1+cu121 --index-url [https://download.pytorch.org/whl/cu121](https://download.pytorch.org/whl/cu121)
```

## 3. ติดตั้ง Dependencies ทั้งหมด
สร้างไฟล์ requirements.txt และใส่ข้อมูลตามนี้ (เวอร์ชันเหล่านี้ถูกทดสอบแล้วว่าทำงานร่วมกันได้ 100%):
```
fastapi
uvicorn==0.42.0
pydantic
pymongo
python-dotenv
pythainlp
pandas
requests
transformers==4.40.0
tokenizers==0.19.1
tqdm==4.67.3
```
รันคำสั่งติดตั้ง:
```
pip install -r requirements.txt
```
## 4. การตั้งค่า Environment Variables
สร้างไฟล์ .env ไว้ที่โฟลเดอร์หลัก (/Python) และกำหนดค่า:
```
MONGO_URI=""
DB_NAME=""
COLLECTION_NAME=""
```

# วิธีเรียกใช้งาน (Execution Guide)

## 1. เตรียมพร้อมระบบ LLM (Ollama)
เปิดโปรแกรม Ollama ให้ทำงานอยู่เบื้องหลัง (รัน Server ที่พอร์ต 11434 โดยอัตโนมัติ) และมั่นใจว่าโหลดโมเดลเรียบร้อย:
```
ollama run qwen2.5:7b
```

## 2.อัปโหลดข้อมูลความรู้ลง MongoDB (ทำแค่ครั้งแรก)
ก่อนใช้งาน RAG ต้องนำข้อมูลจากโฟลเดอร์ /data ขึ้นไปฝังบน Database ก่อน:
```
python embed_to_mongo.py
```
## 3: เปิดเซิร์ฟเวอร์ Backend
เมื่อทุกอย่างพร้อม ให้รัน FastAPI:
```
fastapi dev app.py
```
#### เซิร์ฟเวอร์จะพร้อมทำงานที่ http://127.0.0.1:8000 (รับ API ทาง POST: /api/chat) 
