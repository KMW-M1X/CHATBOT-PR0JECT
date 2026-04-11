from pythainlp.tokenize import word_tokenize
from pythainlp.corpus.common import thai_stopwords
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
import re

# เป้าหมาย: โหลดโมเดล WangchanBERTa แบบ Manual เพื่อแก้ปัญหาไลบรารีตีกัน
print("กำลังโหลด WangchanBERTa NLP Module...")
model_name = "airesearch/wangchanberta-base-att-spm-uncased"
revision = "finetuned@thainer-ner" # ใช้เวอร์ชันที่เทรนมาเพื่อจับคำเฉพาะ (NER)

tokenizer = AutoTokenizer.from_pretrained(model_name, revision="main")
model = AutoModelForTokenClassification.from_pretrained(model_name, revision=revision)

# เป้าหมาย: สร้าง Pipeline NER โดยใช้ aggregation_strategy แทนคำสั่งเก่า
ner_pipeline = pipeline(
    "ner", 
    model=model, 
    tokenizer=tokenizer, 
    aggregation_strategy="simple"
)

def analyze_user_input(text):
    # เป้าหมาย: ตัดคำและคัดกรองคำฟุ่มเฟือยเพื่อหา Keyword
    words = word_tokenize(text, engine="newmm")
    stopwords = list(thai_stopwords())
    keywords = [w for w in words if w not in stopwords and w.strip() != ""]

    # เป้าหมาย: ดึงชื่อเฉพาะและป้ายกำกับจากประโยค
    entities = ner_pipeline(text)
    
    # เป้าหมาย: สกัดตัวเลขจากข้อความเพื่อใช้เป็นเงื่อนไขกรองข้อมูล
    numbers = re.findall(r'\d+', text)
    constraints = [float(n) for n in numbers] if numbers else []

    # เป้าหมาย: จัดหมวดหมู่เจตนาของผู้ใช้
    intent = "Unknown"
    food_words = ["กิน", "หิว", "แคล", "แคลอรี", "เมนู", "อาหาร", "โปรตีน", "น้ำตาล", "ไขมัน"]
    exercise_words = ["ออกกำลัง", "วิ่ง", "เผาผลาญ", "ลดน้ำหนัก", "met", "จักรยาน", "เหนื่อย"]
    
    if any(k in words for k in food_words):
        intent = "Recommend_Food"
    elif any(k in words for k in exercise_words):
        intent = "Calculate_Exercise"

    return {
        "original_text": text,
        "intent": intent,
        "keywords": keywords,
        "constraints": constraints,
        "entities": entities
    }