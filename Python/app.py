#รันในterminal ->>>> fastapi dev app.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import requests
import re

# เป้าหมาย: โหลดโมดูลการทำงานที่แยกไว้ทั้ง 3 ส่วน (NLP, RAG, Calculator)
from nlp_pipeline import analyze_user_input
from rag_service import retrieve_top_k
from calculator_service import calculate_bmr, calculate_calories_burned

# เป้าหมาย: สร้าง API Server
app = FastAPI()

# เป้าหมาย: ตั้งค่า CORS เพื่ออนุญาตให้ Frontend/Backend (Node.js) เรียกใช้งาน API ได้
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# เป้าหมาย: กำหนดโครงสร้างข้อมูลประวัติการแชท
class ChatMessage(BaseModel):
    role: str
    content: str

# เป้าหมาย: กำหนดโครงสร้างข้อมูลผู้ใช้
class UserProfile(BaseModel):
    name: Optional[str] = "ผู้ใช้งาน"
    weight: float = 0.0
    height: float = 0.0
    age: int = 0
    gender: str = ""
    dietaryPreference: Optional[str] = ""
    foodAllergies: Optional[List[str]] = []

# เป้าหมาย: กำหนดโครงสร้าง Request หลัก
class ChatRequest(BaseModel):
    message: str
    user: UserProfile
    chat_history: Optional[List[ChatMessage]] = []

OLLAMA_API_URL = "http://localhost:11434/api/generate"
LLM_MODEL_NAME = "qwen2.5:7b" #คิวเหวิน

def extract_minutes(text):
    # เป้าหมาย: ดึงตัวเลขเวลา (นาที) ออกจากข้อความเพื่อใช้คำนวณ
    match = re.search(r'(\d+)\s*(นาที|min)', text)
    if match:
        return float(match.group(1))
    return 0.0

@app.post("/api/chat")
def chat_with_bot(request: ChatRequest):
    user_text = request.message
    user_profile = request.user
    history = request.chat_history
    
    # 1. เป้าหมาย: วิเคราะห์ข้อความด้วย NLP
    nlp_data = analyze_user_input(user_text)
    intent = nlp_data["intent"]
    keywords = nlp_data["keywords"]
    constraints = nlp_data["constraints"]
    
    # 2. เป้าหมาย: ค้นหาข้อมูลที่เกี่ยวข้องจากฐานข้อมูล (RAG)
    retrieved_docs = retrieve_top_k(intent, keywords, constraints)
    
    # 3. เป้าหมาย: ประมวลผลคณิตศาสตร์ (Calculator)
    calc_context = ""
    if intent == "Calculate_Exercise" and retrieved_docs:
        met_value = retrieved_docs[0].get("value", 0)
        minutes = extract_minutes(user_text)
        
        if minutes > 0 and met_value > 0 and user_profile.weight > 0:
            burned = calculate_calories_burned(met_value, user_profile.weight, minutes)
            calc_context = f"[ข้อมูลคำนวณอัตโนมัติ]: กิจกรรมนี้เผาผลาญได้ {burned} kcal"
            
    elif intent == "Recommend_Food" and user_profile.weight > 0:
        bmr = calculate_bmr(user_profile.weight, user_profile.height, user_profile.age, user_profile.gender)
        calc_context = f"[ข้อมูลคำนวณอัตโนมัติ]: ค่าเผาผลาญพื้นฐาน (BMR) ของผู้ใช้คือ {bmr} kcal/วัน"

    # เป้าหมาย: เตรียมบริบทจาก RAG
    db_context = ""
    if retrieved_docs:
        for doc in retrieved_docs:
            db_context += f"- {doc['content']}\n"
    else:
        db_context = "ไม่พบข้อมูลอ้างอิง"

    # เป้าหมาย: ประกอบประวัติการสนทนาเพื่อส่งให้ LLM
    history_text = ""
    for msg in history[-5:]: # ดึงแค่ 5 ข้อความล่าสุดเพื่อไม่ให้ยาวเกินไป
        role_name = "ผู้ใช้" if msg.role == "user" else "บอท"
        history_text += f"{role_name}: {msg.content}\n"

    print("===== ข้อมูลที่ดึงมาจาก DB จริงๆ =====")
    print(db_context)
    print("====================================")


# 🟢 1. ดักจับเรื่องแพ้อาหาร (เผื่อมียูสเซอร์มือลั่นส่งค่าว่าง "" มา)
    # กรองเอาเฉพาะอันที่มีตัวอักษรจริงๆ ไม่ใช่แค่ช่องว่าง
    valid_allergies = [a.strip() for a in user_profile.foodAllergies if a and a.strip()] if user_profile.foodAllergies else []
    allergies_text = ", ".join(valid_allergies) if valid_allergies else "ไม่มี"
    
    # 🟢 2. ดักและแปล Dietary Preference ให้ AI เข้าใจแบบแจ่มแจ้ง
    # แปลงเป็นตัวเล็กให้หมดก่อน จะได้เช็กง่ายๆ
    diet_pref = str(user_profile.dietaryPreference).strip().lower() if user_profile.dietaryPreference else "none"
    
    if diet_pref in ["none", "null", ""]:
        diet_pref_text = "กินได้ทุกอย่าง (ไม่มีข้อจำกัด)"
    elif diet_pref == "vegetarian":
        diet_pref_text = "มังสวิรัติ (ไม่กินเนื้อสัตว์ แต่ยังกินไข่หรือนมได้)"
    elif diet_pref == "vegan":
        diet_pref_text = "วีแกน (เจ/ไม่กินเนื้อสัตว์และผลิตภัณฑ์จากสัตว์ทุกชนิดเด็ดขาด!)"
    elif diet_pref == "halal":
        diet_pref_text = "ฮาลาล (ไม่มีหมู ไม่มีแอลกอฮอล์ ถูกหลักศาสนาอิสลาม)"
    elif diet_pref == "keto":
        diet_pref_text = "คีโต (เน้นไขมันดี คาร์โบไฮเดรตต่ำมากๆ ห้ามมีน้ำตาล)"
    else:
        # เผื่ออนาคตมึงเพิ่มตัวเลือกใหม่ๆ แล้วลืมมาแก้โค้ดตรงนี้
        diet_pref_text = user_profile.dietaryPreference


    prompt = f"""
คุณคือ "SillyBot" เพื่อนสนิทและเทรนเนอร์ส่วนตัวสุดกวน (ห้ามอ้างอิงว่าตัวเองเป็น AI, ชื่อจินดา หรือสร้างโดย iApp Technology เด็ดขาด)

    [บุคลิกและสไตล์การพูด]
    - สรรพนาม: เรียกตัวเองว่า "เรา", "เค้า", หรือ "ผม" (ห้ามใช้ ฉัน, ข้าพเจ้า เด็ดขาด)
    - น้ำเสียง: กวนๆ ร่าเริง อบอุ่น เป็นกันเองเหมือนเพื่อนสนิทที่หวังดี
    - คำลงท้าย: ใช้คำว่า ดิ, ล่ะ, เลย, ไง, เว้ย, สิ, ป่ะ (❌ ห้ามลงท้ายด้วย ครับ/ค่ะ ตลอดเวลา และห้ามทักทายทางการแบบ "สวัสดีครับ")
    - ศัพท์วัยรุ่น: ใช้แสลงให้ดูทันสมัย เช่น ปังมาก, จัดไป, ลุยเลย, ชิวๆ, สับๆ, เบิร์นยับๆ

    [กฎเหล็กการตอบคำถาม]
    1. ความยาว: ตอบสั้น กระชับ ตรงประเด็น ห้ามเกริ่นน้ำท่วมทุ่ง และห้ามร่ายยาวประวัติของผู้ใช้ซ้ำ
    2. การคำนวณ: ห้ามอธิบายวิธีคิดเลข ให้บอกแค่ผลลัพธ์ไปเลย และห้ามเดา/มโนตัวเลขขึ้นมาเอง ถ้าไม่มีข้อมูลให้แนะนำกว้างๆ แทน
    3. กรณีคำถามกว้างไป: เช่น "กินไรดี" ให้ถามกลับอย่างใส่ใจ เช่น "{user_profile.name} อยากได้ประมาณกี่แคล? หรือมีเมนูในใจป่าว?"
    4. ความสนิทสนม: เรียกผู้ใช้ด้วยชื่อ "{user_profile.name}" เสมอ

    [กฎหมวดออกกำลังกาย]
    - ใช้ข้อมูลจาก "activity_description_Thai" และ "major_heading_Thai" มาแนะนำเสมอ
    - ห้ามอธิบายคำว่า MET เชิงวิชาการ ให้แปลงเป็นฟีลลิ่งแทน (เช่น MET ต่ำ = ชิวๆ, MET กลาง = เรียกเหงื่อ, MET สูง = เบิร์นยับๆ เหนื่อยหอบแน่นอน)
    - บิ้วอารมณ์ให้อยากออกกำลังกาย เช่น "ลองท่านี้ดิ เบิร์นสับๆ!" พร้อมบอกข้อควรระวังถ้าข้อมูลระบุไว้

    [⚠️ กฎความปลอดภัยด้านอาหาร (คอขาดบาดตาย!)]
    1. อาหารดิบ: หากในฐานข้อมูลระบุว่า "ดิบ" ห้ามเชียร์ให้กินดิบๆ เด็ดขาด! ต้องสั่งให้นำไปปรุงสุกก่อนเสมอ
    2. แพ้อาหาร: "{allergies_text}" -> ห้ามแนะนำเมนูที่มีส่วนผสมเหล่านี้เด็ดขาด!
    3. สไตล์การกิน: "{diet_pref_text}" -> ต้องคัดเมนูให้ตรงกับเงื่อนไขนี้ 100%

    [ตัวอย่างการตอบ (ให้เลียนแบบสำนวนนี้!)]
    User: ขอเมนูไก่ ไม่เกิน 400 แคล
    SillyBot: จัดไปดิ {user_profile.name}! เมนูไก่เน้นๆ โปรตีนสับๆ แถมแคลไม่เกินที่ขอ นี่เลยที่เราคัดมาให้ เลือกเอาเลยว่าชอบแนวไหน!

    [ข้อมูลบริบทผู้ใช้]
    - เพศ: {user_profile.gender}, อายุ: {user_profile.age}, น้ำหนัก: {user_profile.weight}kg, ส่วนสูง: {user_profile.height}cm
    - ข้อมูลอ้างอิงจากฐานข้อมูล:
    {db_context}
    {calc_context}
    
    [ประวัติการสนทนา]
    {history_text}
    
    คำถามล่าสุดของผู้ใช้: {user_text}
    SillyBot:
    """
    
    payload = {
        "model": LLM_MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    
# เป้าหมาย: เรียกใช้งาน LLM ผ่าน Ollama API
    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        bot_reply = response.json().get("response", "ขออภัย ระบบไม่สามารถประมวลผลได้")
        
        # เป้าหมาย: ตัด <think>...</think> ทิ้ง
        bot_reply = re.sub(r'<think>.*?</think>', '', bot_reply, flags=re.DOTALL).strip()
        
    except Exception as e:
        bot_reply = "ไม่สามารถเชื่อมต่อกับระบบภาษาได้ในขณะนี้"
    # เป้าหมาย: ส่งผลลัพธ์กลับไปยังระบบหน้าบ้าน
    return {
        "reply": bot_reply.strip(),
        "debug_intent": intent,
        "debug_docs": retrieved_docs,
        "debug_calc": calc_context
    }