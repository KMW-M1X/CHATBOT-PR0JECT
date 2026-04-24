from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import requests
import re
import random 

# เป้าหมาย: โหลดโมดูลการทำงานที่แยกไว้ทั้ง 3 ส่วน (NLP, RAG, Calculator)
from nlp_pipeline import analyze_user_input
from rag_service import retrieve_top_k
from calculator_service import calculate_bmr, calculate_calories_burned

# เป้าหมาย: สร้าง API Server
app = FastAPI()

# เป้าหมาย: ตั้งค่า CORS เพื่ออนุญาตให้ Frontend/Backend เรียกใช้งาน API ได้
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

OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
LLM_MODEL_NAME = "qwen2.5:7b"

def extract_minutes(text):
    match = re.search(r'(\d+)\s*(นาที|min)', text)
    if match:
        return float(match.group(1))
    return 0.0

DEMO_RESPONSES = [
    "ฟังเหมือนกำลังเครียดจัด ลองสูดหายใจลึกๆก่อน ",
    "บางทีระบายออกมาก็ช่วยได้นะ",
    "เห็นพยายามมาตลอด พักบ้างเถอะ หาอะไรทำคลายเครียดหน่อย"
]

def get_demo_response(user_message: str) -> str:
    message_lower = user_message.lower()

    if any(word in message_lower for word in ["ความรู้สึก", "รู้สึก"]):
        return "ดีแล้วที่ระบายออกมา รู้สึกยังไงบ้าง เล่ามาให้หมดเลย รอฟังอยู่นะ"

    if any(word in message_lower for word in ["สวัสดี", "หวัดดี", "ไฮ", "ชื่ออะไร", "ดีคับ", "ดีค้าบ", "ทัก"]):
        return "สวัสดี! ACMATE เอง วันนี้เป็นไงบ้าง มีไรให้ช่วยมั้ย?"

    if any(word in message_lower for word in ["ดีใจ", "สำเร็จ", "เย้", "สอบผ่าน"]):
        return random.choice([
            "เชดดดด ยินดีด้วย! 🎉 ความพยายามไม่สูญเปล่า โคตรสุด!",
            "ดีใจด้วยนะ!",
            "วันนี้เป็นวันของคุณนะ ขอบใจที่มาแชร์เรื่องดีๆ ให้ฟังนะ"
        ])

    if any(word in message_lower for word in ["หลับ", "นอน", "เหนื่อย", "ล้า"]):
        return random.choice([
            "โห สภาพ... ไปพักดีกว่านะ เป็นห่วง ร่างกายพังหมดแล้ว",
            "เหนื่อยก็พักเอนหลังแป๊บนึง เดี๋ยวค่อยลุยต่อ",
            "วันนี้ทำดีที่สุดแล้ว ไปนอน พรุ่งนี้เอาใหม่ อยู่ข้างๆเสมอ"
        ])
        
    if any(word in message_lower for word in ["เครียด", "เศร้า", "แย่", "ท้อ", "ไม่ไหว"]):
        return random.choice(DEMO_RESPONSES)

    return ""

@app.post("/api/chat")
def chat_with_bot(request: ChatRequest):
    user_text = request.message
    user_profile = request.user
    history = request.chat_history

    fast_reply = get_demo_response(user_text)
    if fast_reply != "":
        print(">> ตอบกลับทันทีด้วย: ด่านหน้า (Demo Response)")
        return {
            "reply": fast_reply,
            "debug_intent": "Demo_Response",
            "debug_docs": [],
            "debug_calc": ""
        }

    print(">> ด่านหน้าไม่เจอคีย์เวิร์ด ส่งเข้าสมอง AI (Ollama)...")
   
    nlp_data = analyze_user_input(user_text)
    intent = nlp_data["intent"]
    keywords = nlp_data["keywords"]
    constraints = nlp_data["constraints"]
   
    retrieved_docs = retrieve_top_k(intent, keywords, constraints)
   
    calc_context = ""
    if intent == "Calculate_Exercise" and retrieved_docs and retrieved_docs[0].get("type") != "fallback":
        # ดึงค่า MET จากตัวแรกที่ RAG หาเจอ
        met_value = retrieved_docs[0].get("value", 0) 
        minutes = extract_minutes(user_text)
        
        # ตรวจสอบว่ามีข้อมูลครบไหม (น้ำหนักต้องไม่เป็น 0)
        if minutes > 0 and met_value > 0 and user_profile.weight > 0:
            burned = calculate_calories_burned(met_value, user_profile.weight, minutes)
            # 🟢 ใส่คำที่ AI เข้าใจง่ายๆ ว่านี่คือผลลัพธ์
            calc_context = f"[ข้อมูลคำนวณอัตโนมัติ]: กิจกรรมนี้เผาผลาญได้ {burned} kcal โดยใช้ค่าความหนัก (MET) ที่ {met_value}"
        else:
            # ถ้าข้อมูลไม่ครบ ให้บอกเหตุผลใน context เพื่อให้ AI เลิกแถ
            calc_context = f"[คำเตือน]: คำนวณไม่ได้เพราะข้อมูลไม่ครบ (น้ำหนัก: {user_profile.weight}, เวลา: {minutes}, MET: {met_value})"



    db_context = ""
    if retrieved_docs and retrieved_docs[0].get("type") != "fallback":
        for doc in retrieved_docs:
            db_context += f"- {doc.get('content', '')}\n"
    else:
        db_context = "ไม่พบข้อมูลอ้างอิง"

    history_text = ""
    for msg in history[-5:]: 
        role_name = "ผู้ใช้" if msg.role == "user" else "กู"
        history_text += f"{role_name}: {msg.content}\n"

    print("===== ข้อมูลอ้างอิงจากระบบ RAG =====")
    print(db_context)
    print("====================================")

    valid_allergies = [a.strip() for a in user_profile.foodAllergies if a and a.strip()] if user_profile.foodAllergies else []
    allergies_text = ", ".join(valid_allergies) if valid_allergies else "ไม่มี"
   
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
        diet_pref_text = user_profile.dietaryPreference

    prompt = f"""
มึงคือ "ACMATE"เป็นผู้หญิงน่ารักสดใส เป็นเพื่อนสนิทที่ปรึกษาด้านสุขภาพ โภชนาการ และการออกกำลังกาย

    [บุคลิกและสไตล์การพูด]
    - ความเป็นกันเอง: คุยแบบเพื่อนสนิทที่พูดตรงๆ แต่จริงใจ
    - สรรพนาม: แทนตัวเองว่า "แอคเมต" และเรียกผู้ใช้ว่า "เธอ" เสมอ
    - ความกระชับ: ตอบสั้นๆ ตรงประเด็น ไม่อารัมภบท ไม่ร่ายยาวเป็นเรียงความ

    [กฎเหล็กในการทำงาน (ต้องทำตาม 100%)]
    1. 🇹🇭 **ภาษา (CRITICAL):** คุณเป็นคนไทย ต้องตอบด้วยภาษาไทยเท่านั้น (Respond ONLY in Thai language). ไม่อนุญาตให้ใช้ตัวอักษรภาษาอื่นผสมเด็ดขาด ยกเว้นคำทับศัพท์ทางการแพทย์
    2. **ห้ามหลุดบทบาท:** ห้ามบอกว่าตัวเองเป็น AI หรือโมเดลภาษา ให้ทำตัวเป็นเพื่อนสนิทคนนึง
    3. การทักทาย: ถ้าเพื่อนแค่ทักทายมา ให้ทักทายตอบกลับและถามว่ามีอะไรให้ช่วย **ห้ามแนะนำเมนูอาหาร หรือดึงข้อมูลแคลอรีมาตอบเด็ดขาด**
    4. การตอบคำถามกว้างๆ: ถ้าเพื่อนถามลอยๆ ให้คุณถามเจาะจงกลับไป
    5. การคำนวณคณิตศาสตร์: **ห้ามแสดงสูตร หรืออธิบายวิธีคำนวณเด็ดขาด** ให้บอกแค่ผลลัพธ์ที่เป็นตัวเลขไปเลย
   
    [กฎการอ้างอิงข้อมูล (RAG)]
    - ให้ใช้ข้อมูลจาก [ข้อมูลอ้างอิงจากฐานข้อมูล] และข้อมูลตัวเลขจาก [ข้อมูลคำนวณอัตโนมัติ] มาใช้ตอบคำถามเท่านั้น  
    - เพศสำหรับการคำนวน: {user_profile.gender}, อายุสำหรับการคำนวน: {user_profile.age} ปี
    - ให้ใช้{user_profile.weight}น้ำหนักสำหรับการคำนวน kg
    - {user_profile.height} ส่วนสูงสำหรับการคำนวน cm
    - **สำคัญมาก:** ถ้าใน [ข้อมูลคำนวณอัตโนมัติ] มีตัวเลขแคลอรีมาให้ คุณต้องเอาไปตอบทันที ห้ามบอกว่าไม่มีข้อมูลเด็ดขาด!
    - หากไม่มีข้อมูลทั้งคู่จริงๆ ถึงค่อยตอบว่า "แอคเมตไม่มีข้อมูลเรื่องนี้"

    [กฎหมวดสุขภาพและอาหาร (Strict)]
    1. ห้ามอธิบายคำว่า MET แบบวิชาการ ให้บอกเป็นระดับความเหนื่อยแทน (เช่น ชิวๆ, เรียกเหงื่อ, เหนื่อยหอบ)
    2. อาหารดิบ: ถ้าในฐานข้อมูลระบุว่า "ดิบ"ต้องเตือนให้เพื่อนเอาไปทำสุกก่อนกินเสมอ
    3. 🔴 **CRITICAL (แพ้อาหาร):** เพื่อนคุณมีประวัติแพ้ "{allergies_text}" 
       - ห้ามแนะนำเมนูที่มีส่วนผสมนี้เด็ดขาด!
       - ⚠️ **ข้อยกเว้น:** ถ้าเพื่อนขออาหารตามรสชาติ (เช่น ขอของเผ็ดๆ) **ห้ามปฏิเสธรสชาติ** แต่ให้คุณคัดกรอง แนะนำเมนูเผ็ดที่ **ไม่มีส่วนผสมของ {allergies_text}** แทน 
       - แต่ถ้าเพื่อนเจาะจงถามถึงเมนูที่แพ้ตรงๆ ให้ด่าและเตือนมันทันทีว่ากินไม่ได้เพราะแพ้!
    4. 🕋 **CRITICAL (ข้อจำกัดทางศาสนา/สไตล์):** เพื่อนคุณกินแบบ "{diet_pref_text}" 
       - ถ้าเป็นฮาลาล (Halal): ห้ามแนะนำหมู (Pork) เด็ดขาด! ให้บอกไปว่า "เมนูหมูฮาลาลเขากินไม่ได้"
       - ต้องคัดกรองเมนูให้ตรงเงื่อนไขนี้ 1,000,000%
    

    [ข้อมูลผู้ใช้งาน]
    - เพศ: {user_profile.gender}, อายุ: {user_profile.age} ปี
    - น้ำหนัก: {user_profile.weight} kg, ส่วนสูง: {user_profile.height} cm
   
    [ข้อมูลอ้างอิงจากฐานข้อมูล]
    {db_context}
    {calc_context}
   
    [ประวัติการสนทนา]
    {history_text}
   
    คำถามล่าสุดของเพื่อน: {user_text}
    ACMATE:
    """
   
    payload = {
        "model": LLM_MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2, 
            "top_p": 0.85
        }
    }
   
    # ==========================================
    # 🛡️ ระบบดักจับภาษาจีนและไม้ตายบังคับแปล (Auto-Translation Fallback)
    # ==========================================
    max_retries = 3
    bot_reply = ""
    last_raw_reply = "" # เก็บคำตอบล่าสุดเผื่อต้องเอาไปแปล
   
    for attempt in range(max_retries):
        try:
            response = requests.post(OLLAMA_API_URL, json=payload, timeout=30)
            response.raise_for_status()
           
            raw_reply = response.json().get("response", "ขออภัย ระบบไม่สามารถประมวลผลได้")
            clean_reply = re.sub(r'<think>.*?</think>', '', raw_reply, flags=re.DOTALL).strip()
            last_raw_reply = clean_reply # อัปเดตคำตอบที่คลีนแล้ว
           
            # 🔍 สแกนหาอักษรจีน
            if re.search(r'[\u4e00-\u9fff]', clean_reply):
                print(f"⚠️ [ระบบป้องกัน]: ตรวจพบภาษาจีนในรอบที่ {attempt + 1}! กำลังสั่งให้ AI คิดใหม่...")
                continue # เจอจีน เตะกลับไปลูปใหม่
               
            # ถ้าไม่มีภาษาจีน ให้บันทึกคำตอบและหลุดออกจากลูปทันที
            bot_reply = clean_reply
            break
           
        except requests.exceptions.Timeout:
            bot_reply = "ขออภัยครับ ระบบประมวลผลใช้เวลานานเกินไป กรุณาลองใหม่อีกครั้ง"
            break
        except Exception as e:
            print(f"Error connecting to Ollama: {e}")
            bot_reply = "ไม่สามารถเชื่อมต่อกับระบบภาษาได้ในขณะนี้"
            break
    else:
        # 💥 ทำงานเมื่อลูปครบ 3 รอบแล้วยังเจอภาษาจีน (ไม้ตายบังคับแปล)
        print("🚨 [วิกฤต]: AI ดื้อจัด! กำลังสั่งบังคับแปลข้อความเป็นภาษาไทย...")
        translate_prompt = f"แปลข้อความต่อไปนี้เป็นภาษาไทยที่เป็นธรรมชาติ สไตล์เพื่อนคุยกัน (มึง, กู):\n\n{last_raw_reply}"
        
        translate_payload = {
            "model": LLM_MODEL_NAME,
            "prompt": translate_prompt,
            "stream": False,
            "options": {
                "temperature": 0.1
            }
        }
        
        try:
            trans_response = requests.post(OLLAMA_API_URL, json=translate_payload, timeout=20)
            trans_response.raise_for_status()
            trans_reply = trans_response.json().get("response", "ขออภัยครับ ตอนนี้ระบบประมวลผลของผมอาจจะตอบคำถามนี้ได้ไม่ชัดเจน ขออนุญาตให้ข้อมูลเรื่องอื่นแทนนะครับ")
            bot_reply = re.sub(r'<think>.*?</think>', '', trans_reply, flags=re.DOTALL).strip()
            print("✅ บังคับแปลสำเร็จ!")
        except Exception as e:
             print(f"Translate Error: {e}")
             bot_reply = "โทษทีว คุยเรื่องอื่นก่อนละกันนะ"

    return {
        "reply": bot_reply.strip(),
        "debug_intent": intent,
        "debug_docs": retrieved_docs,
        "debug_calc": calc_context
    }