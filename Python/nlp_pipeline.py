import torch
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
import os
import re
from pythainlp.tokenize import word_tokenize
from pythainlp.corpus.common import thai_stopwords

# --- ส่วนที่ 1: เลือก Device (Universal สำหรับ PC และ Mac) ---
if torch.cuda.is_available():
    device_id = 0 
    print("🧠 NLP Module: ใช้ CUDA")
elif torch.backends.mps.is_available():
    device_id = 0 
    print("🍏 NLP Module: ใช้ Apple Silicon (MPS)")
else:
    device_id = -1 # CPU
    print("🐢 NLP Module: ใช้ CPU")

print("กำลังโหลด WangchanBERTa NLP Module...")
model_name = "airesearch/wangchanberta-base-att-spm-uncased"
revision = "finetuned@thainer-ner"

tokenizer = AutoTokenizer.from_pretrained(model_name, revision="main")
model = AutoModelForTokenClassification.from_pretrained(model_name, revision=revision)

# ใส่ device=device_id เข้าไปใน pipeline เพื่อความไว
ner_pipeline = pipeline(
    "ner", 
    model=model, 
    tokenizer=tokenizer, 
    aggregation_strategy="simple",
    device=device_id
)

def analyze_user_input(text):
    # --- ส่วนที่ 1: ตัดคำและหา Keywords ---
    words = word_tokenize(text, engine="newmm")
    stopwords = list(thai_stopwords())
    keywords = [w for w in words if w not in stopwords and w.strip() != ""]

    # --- ส่วนที่ 2: ดึงชื่อเฉพาะ (Entities) ---
    # ⚠️ ถ้า Mac 8GB รันไม่ไหว ให้ใส่เครื่องหมาย # หน้าบรรทัดล่างนี้ แล้วแก้เป็น entities = []
    entities = ner_pipeline(text)
    
    # --- ส่วนที่ 3: สกัดตัวเลข (Constraints) ---
    numbers = re.findall(r'\d+', text)
    constraints = [float(n) for n in numbers] if numbers else []

    # --- ส่วนที่ 4: จัดหมวดหมู่เจตนา (Intent) แบบ Scoring System ---
    intent = "Unknown"
    text_lower = text.lower() # เช็กแบบตัวเล็กทั้งหมด
    
    # 1. แยกคีย์เวิร์ดที่เป็นเอกลักษณ์ของแต่ละฝั่งให้ชัดเจน (เอาคำว่า แคล ออกไปก่อน)
    food_keywords = ["กิน", "หิว", "เมนู", "อาหาร", "โปรตีน", "น้ำตาล", "ไขมัน", "มื้อ", "สูตร"]
    exercise_keywords = ["ออกกำลัง", "วิ่ง", "ปั่น", "จักรยาน", "เผาผลาญ", "ลดน้ำหนัก", "met", "mets", "เหนื่อย", "เดิน", "ว่ายน้ำ"]
    
    # 2. นับคะแนนว่าประโยคนี้เอนเอียงไปทางไหน
    food_score = sum(1 for k in food_keywords if k in text_lower)
    exercise_score = sum(1 for k in exercise_keywords if k in text_lower)

    # 3. จัดการคำกำกวม (คำว่า แคล / แคลอรี)
    if "แคล" in text_lower or "แคลอรี" in text_lower:
        if "เผาผลาญ" in text_lower or exercise_score > 0:
            exercise_score += 2 # ถ้ามีคำว่าเผาผลาญด้วย แปลว่าถามเรื่องออกกำลังกายชัวร์!
        else:
            food_score += 1     # ถ้าพูดแคลลอยๆ ให้เดาว่าเป็นเรื่องของกิน

    # 4. ตัดสินผลแพ้ชนะ
    if exercise_score > food_score:
        intent = "Calculate_Exercise"
    elif food_score > exercise_score:
        intent = "Recommend_Food"
    elif "คืออะไร" in text_lower or "แนะนำ" in text_lower:
        intent = "Health_Advice"
    else:
        # ถ้าคะแนนเท่ากัน หรือตีความไม่ได้ ให้โยนเข้าโหมดความรู้ทั่วไป (RAG)
        intent = "Health_Advice" 

    # ส่งค่ากลับไปให้ app.py และ rag_service.py ใช้งาน
    return {
        "original_text": text,
        "intent": intent,
        "keywords": keywords,
        "constraints": constraints,
        "entities": entities
    }