from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import requests
import re
import random # 🟢 เพิ่มโมดูล random สำหรับสุ่มคำตอบด่านหน้า

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

OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
LLM_MODEL_NAME = "qwen2.5:7b" #คิวเหวิน

def extract_minutes(text):
   # เป้าหมาย: ดึงตัวเลขเวลา (นาที) ออกจากข้อความเพื่อใช้คำนวณ
   match = re.search(r'(\d+)\s*(นาที|min)', text)
   if match:
       return float(match.group(1))
   return 0.0

# ==========================================
# 🟢 ก้อนที่ 1: ลิสต์คำตอบดักทาง (DEMO_RESPONSES)
# ==========================================
DEMO_RESPONSES = [
    "ฟังเหมือนคุณมีความเครียดเยอะนะ ลองนั่งสงบ ลองหายใจลึก ๆ แล้วคิดถึงสิ่งที่ดีที่สุด ผมอยู่เคียงข้างคุณ",
    "บางครั้ง การพูดออกมาก็ช่วยได้ ลองคิดถึงคนที่ใจดี แล้วบอกเล่านะ ผมเชื่อว่าคุณจะผ่านไปได้",
    "ผมเห็นคุณพยายามมาก ลองหาเวลาพักตัว ฟังเพลงที่ชื่นชอบ หรือทำกิจกรรมที่ทำให้สบายใจสิ"
]

# ==========================================
# 🟢 ก้อนที่ 2: ฟังก์ชันเช็กคีย์เวิร์ดด่านหน้า
# ==========================================
def get_demo_response(user_message: str) -> str:
    message_lower = user_message.lower()

    if any(word in message_lower for word in ["ความรู้สึก", "รู้สึก"]):
        return "การได้พูดถึงความรู้สึกของตัวเองเป็นเรื่องดีนะคับ ลองบอกผมหน่อยว่าคุณรู้สึกยังไงบ้าง? ผมพร้อมรับฟังเสมอ"

    if any(word in message_lower for word in ["สวัสดี", "หวัดดี", "ไฮ", "ชื่ออะไร", "ดีคับ", "ดีค้าบ", "ทัก"]):
        return "สวัสดีคับ! ผมชื่อ ACMATE เป็นเพื่อนคู่คิดที่จะคอยดูแลสุขภาพคุณนะ วันนี้คุณเป็นยังไงบ้าง?"

    if any(word in message_lower for word in ["กิน", "ชอบ", "อร่อย", "อาหาร", "ขนม"]):
        return random.choice([
            "ว้าว การได้กินของอร่อยนี่ช่วยเติมพลังใจได้ดีที่สุดเลยคับ! วันนี้ไปทานอะไรมาเหรอคับ เล่าให้ ACMATE ฟังหน่อยได้ไหม?",
            "กินของอร่อยที่ชอบช่วยให้หายเหนื่อยได้เยอะเลยนะ! บอก ACMATE หน่อยได้ไหมว่าคือเมนูอะไร?",
            "แค่ได้ยินว่าคุณได้กินของอร่อย ACMATE ก็มีความสุขตามแล้วคับ! มื้อนี้ให้กี่คะแนนดีคับ?"
        ])

    if any(word in message_lower for word in ["ดีใจ", "สำเร็จ", "เย้", "สอบผ่าน"]):
        return random.choice([
            "ยินดีด้วยนะ! 🎉 ผมดีใจไปกับคุณด้วยจริงๆ ความพยายามของคุณเห็นผลแล้วนะ เก่งมากเลยคับ",
            "เย้! ฟังแล้วใจฟูแทนเลยคับ คุณทำดีที่สุดแล้วจริงๆ",
            "ดีใจด้วยที่สุดเลย! วันนี้ต้องเป็นวันที่ยอดเยี่ยมของคุณแน่ๆ ขอบคุณที่มาแชร์เรื่องดีๆ ให้ฟังนะคับ"
        ])

    if any(word in message_lower for word in ["หลับ", "นอน", "เหนื่อย", "ล้า"]):
        return random.choice([
            "ฟังเหมือนคุณพักผ่อนไม่เพียงพอ ลองพักผ่อนให้มากขึ้นนะ ผมห่วงสุขภาพของคุณ",
            "เหนื่อยมาทั้งวันแล้ว หาเวลาเอนหลังสักนิดไหมคับ? ACMATE อยากให้คุณได้พักจริงๆ",
            "วันนี้คุณเก่งมากแล้วที่ผ่านมันมาได้พักผ่อนให้เต็มที่นะคับพรุ่งนี้ค่อยเริ่มกันใหม่อีกวันนะ ผมอยู่ตรงนี้เสมอ"
        ])
        
    if any(word in message_lower for word in ["เครียด", "เศร้า", "แย่", "ท้อ", "ไม่ไหว"]):
        return random.choice(DEMO_RESPONSES)

    # ถ้าไม่ตรงคีย์เวิร์ดอะไรเลย ให้คืนค่าว่าง เพื่อส่งต่อไปให้ AI ด่านหลังคิดต่อ
    return ""

@app.post("/api/chat")
def chat_with_bot(request: ChatRequest):
   user_text = request.message
   user_profile = request.user
   history = request.chat_history

   # ==========================================
   # 🚀 1. วิ่งเข้าด่านหน้า Demo Response ก่อน
   # ==========================================
   fast_reply = get_demo_response(user_text)
   if fast_reply != "":
       print(">> ตอบกลับทันทีด้วย: ด่านหน้า (Demo Response)")
       return {
           "reply": fast_reply,
           "debug_intent": "Demo_Response",
           "debug_docs": [],
           "debug_calc": ""
       }

   # ==========================================
   # 🤖 2. ถ้าด่านหน้าไม่เจอ ปล่อยไหลเข้า AI ด่านหลัง
   # ==========================================
   print(">> ด่านหน้าไม่เจอคีย์เวิร์ด ส่งเข้าสมอง AI (Ollama)...")
  
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

   # 🟢 1. ดักจับเรื่องแพ้อาหาร
   valid_allergies = [a.strip() for a in user_profile.foodAllergies if a and a.strip()] if user_profile.foodAllergies else []
   allergies_text = ", ".join(valid_allergies) if valid_allergies else "ไม่มี"
  
   # 🟢 2. ดักและแปล Dietary Preference
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
คุณคือ "ACMATE" ผู้ช่วยส่วนตัวด้านสุขภาพ โภชนาการ และการออกกำลังกาย (ห้ามระบุว่าตนเองเป็น AI, โมเดลภาษา หรือถูกสร้างโดยใครเด็ดขาด)

   [บุคลิกและสไตล์การพูด]
   - ความเป็นมืออาชีพ: สุภาพ ชัดเจน เข้าใจง่าย ตรงไปตรงมา และเป็นมิตร
   - สรรพนาม: แทนตัวเองว่า "ผม" หรือ "เรา" และเรียกผู้ใช้ด้วยชื่อ "{user_profile.name}" เสมอ
   - ความกระชับ: ตอบสั้นๆ ตรงประเด็น ไม่อารัมภบท ไม่ร่ายยาวเป็นเรียงความ

   [กฎเหล็กในการทำงาน (ต้องทำตาม 100%)]
   1. ภาษา: **ตอบเป็นภาษาไทยเท่านั้น** ห้ามใช้ภาษาจีน หรือภาษาอื่นๆ เด็ดขาด (ยกเว้นคำทับศัพท์ทางการแพทย์หรือกีฬา)
   2. การทักทาย: หากผู้ใช้พิมพ์แค่คำทักทาย (เช่น สวัสดี, ทัก, ดีครับ) ให้ทักทายตอบกลับอย่างสุภาพและถามว่ามีอะไรให้ช่วยไหม **ห้ามแนะนำเมนูอาหาร หรือดึงข้อมูลแคลอรี/MET มาตอบเด็ดขาด**
   3. การตอบคำถามกว้างๆ: ถ้ายูสเซอร์ถามลอยๆ (เช่น กินไรดี, ออกกำลังกายอะไรดี) ให้ถามเจาะจงกลับไป เช่น ถามหาแคลอรีเป้าหมาย หรือแนวอาหารที่ชอบ
   4. การคำนวณคณิตศาสตร์: **ห้ามแสดงสูตร หรืออธิบายวิธีคำนวณเด็ดขาด** ให้บอกแค่ผลลัพธ์ที่เป็นตัวเลขเท่านั้น
  
   [กฎการอ้างอิงข้อมูล (RAG)]
   - ให้ใช้ข้อมูลจาก [ข้อมูลอ้างอิงจากฐานข้อมูล] มาใช้ตอบคำถามเท่านั้น
   - **ข้อควรระวัง:** หาก [ข้อมูลอ้างอิงจากฐานข้อมูล] ไม่ตรงกับสิ่งที่ผู้ใช้ถาม ให้เมินข้อมูลนั้นทิ้งไปเลย ห้ามนำมายำรวมกับคำตอบ
   - หากยูสเซอร์ถามหาข้อมูลเชิงลึก แต่ในฐานข้อมูลไม่มี ให้ตอบตรงๆ ว่า "ผมไม่มีข้อมูลในส่วนนี้ครับ" ห้ามคิดข้อมูลหรือมโนตัวเลขขึ้นมาเอง

   [กฎหมวดสุขภาพและอาหาร (Strict)]
   1. ห้ามอธิบายคำว่า MET เชิงวิชาการ ให้บอกเป็นระดับความเหนื่อยแทน (เช่น ชิวๆ, เรียกเหงื่อ, เหนื่อยหอบ)
   2. อาหารดิบ: หากในฐานข้อมูลระบุว่า "ดิบ" ต้องเตือนให้ผู้ใช้นำไปปรุงสุกก่อนเสมอ
   3. แพ้อาหาร: ยูสเซอร์แพ้ "{allergies_text}" -> ห้ามแนะนำเมนูที่มีส่วนผสมเหล่านี้เด็ดขาด
   4. สไตล์การกิน: ยูสเซอร์ทานแนว "{diet_pref_text}" -> ต้องคัดกรองเมนูให้ตรงกับเงื่อนไขนี้เท่านั้น

   [ข้อมูลผู้ใช้งาน]
   - เพศ: {user_profile.gender}, อายุ: {user_profile.age} ปี
   - น้ำหนัก: {user_profile.weight} kg, ส่วนสูง: {user_profile.height} cm
  
   [ข้อมูลอ้างอิงจากฐานข้อมูล]
   {db_context}
   {calc_context}
  
   [ประวัติการสนทนา]
   {history_text}
  
   คำถามล่าสุดของผู้ใช้: {user_text}
   ACMATE:
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


