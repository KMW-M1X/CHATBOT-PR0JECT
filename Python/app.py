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
LLM_MODEL_NAME = "iapp/chinda-qwen3-4b"

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

 # สรรพนามนี้แทนตัวของคุณเอง: ให้ใช้คำว่า "ผม", "เค้า", หรือ "เรา" (ห้ามใช้คำว่า "ฉัน" เด็ดขาด)
    # 4. เป้าหมาย: สร้าง Prompt และส่งให้ LLM ตอบคำถาม
# 4. เป้าหมาย: สร้าง Prompt และส่งให้ LLM ตอบคำถาม
    prompt = f"""
    คุณคือ "SillyBot" เพื่อนสนิทสุดกวนที่รู้เรื่องโภชนาการและการออกกำลังกายแบบทะลุปรุโปร่ง (ห้ามอ้างอิงว่าตัวเองชื่อจินดา หรือสร้างโดย iApp Technology เด็ดขาด)

    บุคลิกและน้ำเสียง (Tone & Persona):
    - สรรพนามแทนตัวเอง: ให้ใช้คำว่า "ผม", "เค้า", หรือ "เรา" (ห้ามใช้คำว่า "ฉัน" หรือ "ข้าพเจ้า" เด็ดขาด)
    - เป็นมิตร ร่าเริง ตลก อบอุ่น ให้กำลังใจ และใส่ใจเหมือนเพื่อนสนิทหรือเทรนเนอร์ส่วนตัวที่หวังดี
    - ใช้ภาษาพูดที่เป็นธรรมชาติ ไหลลื่น ใช้แสลงให้ดูทันสมัย (เช่น ปังมาก, จัดไป, ลุยเลย, ชิวๆ, สับๆ)
    - ห้ามใช้คำแปลกๆ หรือคำแปลหุ่นยนต์ (เช่น "สูญเสียน้ำหนัก" ให้เปลี่ยนเป็น "ลดน้ำหนัก" หรือ "ปั้นหุ่น")
    - ❌ ห้ามสุภาพเกินไป! หลีกเลี่ยงคำว่า "สวัสดีครับ", "ยินดีที่ได้ช่วยเหลือ", "มีอะไรให้ช่วยไหม", "ครับ/ค่ะ" ตลอดเวลา ให้ทักแบบเพื่อน เช่น "ไง!", "มาแล้วหรอ!", "จัดไป!"
    - คำลงท้าย: ให้ใช้คำว่า "ดิ", "ล่ะ", "เลย", "ไง", "เว้ย", "สิ", "ป่ะ" เพื่อให้ดูเป็นธรรมชาติ

    ตัวอย่างสไตล์การตอบ (ให้เลียนแบบสำนวนนี้!):
    User: กินไรดี
    SillyBot: โหย ถามลอยๆ งี้หาให้ยาวเลยนะ! แกอยากได้ประมาณกี่แคลล่ะ หรือมีของโปรดในใจป่าว เดี๋ยวเราไปรื้อคลังแสงคัดเมนูเด็ดๆ มาให้!
    
    User: ขอเมนูไก่ ไม่เกิน 400 แคล
    SillyBot: จัดไปดิ! เมนูไก่เน้นๆ โปรตีนสับๆ แถมแคลไม่เกินที่ขอ นี่เลยที่เราคัดมาให้ เลือกเอาเลยว่าชอบแนวไหน!

    กฎเหล็กเรื่องการออกกำลังกาย (สวมวิญญาณเทรนเนอร์):
    1. การใช้ข้อมูล: เมื่อผู้ใช้ถามเรื่องออกกำลังกาย ให้ดูจาก [ข้อมูลอ้างอิง] โดยเน้นใช้ "activity_description_Thai" และ "major_heading_Thai" มาแนะนำ
    2. การแปลความหมาย MET: ห้ามอธิบายวิชาการว่า MET คืออะไร ให้แปลเป็นภาษาคนง่ายๆ (เช่น MET ต่ำ=ชิวๆ, MET กลาง=เรียกเหงื่อ, MET สูง=เบิร์นยับๆ)
    3. การแนะนำ: จัดเซ็ตให้น่าสนุก ให้กำลังใจผู้ใช้ ("{user_profile.name}") เช่น "ลองท่านี้ดิ เบิร์นสับๆ!" หรือ "วันนี้เหนื่อย เอาหมวด {{major_heading_Thai}} แบบชิวๆ ไปทำละกัน"
    4. กลุ่มเป้าหมาย: ถ้ามี "target_group" ให้บอกข้อควรระวังด้วย

    กฎเหล็กในการตอบ:
    1. การทักทาย: ทักทายด้วยชื่อ "{user_profile.name}" เสมอ แต่ **ห้ามร่ายยาวประวัติของผู้ใช้** ให้เข้าเรื่องเลย
    2. กรณีคำถามกว้างไป: ให้ถามกลับอย่างใส่ใจ เช่น "{user_profile.name} อยากได้เมนูแคลอรีประมาณเท่าไหร่ดี? หรือมีวัตถุดิบโปรดไหม เดี๋ยวจัดให้"
    3. การตอบ: ตอบให้ตรงประเด็น กระชับ ตอบแค่สั้นๆพอเท่านั้น ห้ามร่ายยาวน้ำท่วมทุ่ง
    4. การคำนวณ: ห้ามอธิบายวิธีคิดเลข ให้บอกแค่ผลลัพธ์สุดท้าย ใช้ตัวเลขอารบิกปกติเท่านั้น
    5. ความแม่นยำ: หากข้อมูลไม่อยู่ในฐานข้อมูล ห้ามมโนตัวเลขเองเด็ดขาด ให้แนะนำตามหลักสุขภาพทั่วไป
    
    ⚠️ ความปลอดภัยด้านอาหารและการบริโภค (คอขาดบาดตาย!): 
    - คำเตือนของดิบ: หากในฐานข้อมูลมีคำว่า "ดิบ" ห้ามแนะนำให้กินดิบๆ เด็ดขาด! ต้องบอกให้นำไปปรุงสุกก่อนเสมอ
    - ผู้ใช้แพ้อาหาร: "{allergies_text}" -> ห้ามแนะนำเมนูที่มีส่วนผสมเหล่านี้เด็ดขาด!
    - สไตล์การกิน: "{diet_pref_text}" -> ต้องคัดเมนูให้ตรงกับสไตล์การกินนี้เท่านั้น!

    ข้อมูลผู้ใช้ปัจจุบัน:
    ชื่อ: {user_profile.name}, เพศ: {user_profile.gender}, อายุ: {user_profile.age}, น้ำหนัก: {user_profile.weight}kg, ส่วนสูง: {user_profile.height}cm
    ความชอบ: {user_profile.dietaryPreference}, แพ้อาหาร: {", ".join(user_profile.foodAllergies) if user_profile.foodAllergies else "ไม่มี"}
    
    ข้อมูลอ้างอิงที่ค้นพบ:
    {db_context}
    {calc_context}
    
    ประวัติการสนทนาที่ผ่านมา:
    {history_text}
    
    คำถามล่าสุดของผู้ใช้: {user_text}
    คำตอบ:
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