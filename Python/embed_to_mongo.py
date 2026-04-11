import pandas as pd
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import torch
from transformers import AutoTokenizer, AutoModel

# เป้าหมาย: โหลดค่าตัวแปรสภาพแวดล้อม
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

# 🟢 ใช้ GPU ให้เป็นประโยชน์!
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("กำลังโหลดโมเดล Qwen3 ยัดลงการ์ดจอ (Direct Load ไม่ง้อไลบรารีอื่น)...")
# เป้าหมาย: โหลดโมเดลตรงๆ และส่งไปที่ GPU
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-Embedding-0.6B", trust_remote_code=True)
model = AutoModel.from_pretrained("Qwen/Qwen3-Embedding-0.6B", trust_remote_code=True).to(device)

def get_embedding(text):
    # เป้าหมาย: แปลงข้อความเป็น Vector และโยนเข้า GPU
    inputs = tokenizer(text, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    
    # 🟢 เป้าหมาย: อัปเกรดเป็นท่า CLS Pooling + Normalize ให้โคตรแม่น (ท่าเดียวกับที่ใช้ค้นหา)
    embeddings = outputs.last_hidden_state[:, 0]
    embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
    
    return embeddings[0].cpu().tolist()

def safe_float(val):
    # เป้าหมาย: แปลงค่าเป็นทศนิยม 
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0

def upload_to_mongo():
    # เป้าหมาย: เชื่อมต่อฐานข้อมูล
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    
    #print("กำลังเคลียร์พื้นที่ในฐานข้อมูล...")
    #collection.delete_many({})
    
    csv_files = [
        r"D:\Chat Bot Project\Python\data\thai_nutrition.csv",
        r"D:\Chat Bot Project\Python\data\mets_data.csv",
        r"D:\Chat Bot Project\Python\data\health_tips.csv"
    ]

    print("เริ่มกระบวนการฝัง Vector ขั้นเทพ และอัปโหลด...")
    documents = []

    for file_path in csv_files:
        if not os.path.exists(file_path):
            print(f"ไม่พบไฟล์: {file_path}")
            continue

        print(f"กำลังจัดการไฟล์: {os.path.basename(file_path)}")
        df = pd.read_csv(file_path).fillna('')

        for index, row in df.iterrows():
            filename = os.path.basename(file_path)
            
            if "thai_nutrition" in filename.lower():
                item_name = str(row.get('Thai_Name', '')).strip()
                if not item_name or item_name.lower() == 'nan':
                    continue

                food_code = str(row.get('Food_Code', '')).strip()
                english_name = str(row.get('English_Name', '')).strip()
                
                sugar = safe_float(row.get('SUGAR(g)', 0))
                protein = safe_float(row.get('Protein(g)', 0))
                fat = safe_float(row.get('Fat(g)', 0))
                energy = safe_float(row.get('Energy(kcal)', 0))
                carbs = safe_float(row.get('Carbohydrate', 0))
                fibre = safe_float(row.get('fibre', 0))
                
                item_type = "food"
                text_to_embed = f"เมนูอาหาร: {item_name} พลังงาน: {energy} kcal, โปรตีน: {protein}g, คาร์โบไฮเดรต: {carbs}g, ไขมัน: {fat}g"
                
                extra_data = {
                    "food_code": food_code,
                    "english_name": english_name,
                    "calories": energy,
                    "sugar_g": sugar,
                    "protein_g": protein,
                    "fat_g": fat,
                    "carbohydrate_g": carbs,
                    "fibre_g": fibre
                }
                numeric_value = energy
                
            elif "mets_data" in filename.lower():
                item_name = str(row.get('activity_description_Thai', '')).strip()
                if not item_name or item_name.lower() == 'nan':
                    continue

                item_value = str(row.get('met_value', '0')).strip()
                numeric_value = safe_float(item_value)
                
                major_heading_thai = str(row.get('major_heading_Thai', '')).strip()
                activity_desc = str(row.get('activity_description', '')).strip()
                
                item_type = "exercise"
                text_to_embed = f"หมวดหมู่: {major_heading_thai} กิจกรรม: {item_name} ({activity_desc}) ค่า MET: {numeric_value}"
                
                extra_data = {
                    "major_heading_thai": major_heading_thai,
                    "activity_description": activity_desc
                }
            
            # 🟢 [แถมให้] เผื่อมึงจะรัน health_tips.csv กูใส่ดักไว้ให้มันไม่พัง
            elif "health_tips" in filename.lower():
                # มึงต้องไปแก้ชื่อคอลัมน์ให้ตรงกับไฟล์ CSV มึงนะ กูดักไว้คร่าวๆ
                item_name = str(row.get('tip_name', '')).strip()
                if not item_name:
                    continue
                item_type = "health_advice"
                numeric_value = 0.0
                text_to_embed = f"คำแนะนำสุขภาพ: {item_name}"
                extra_data = {}
                
            else:
                continue

            # ส่งไปแปลงเป็นตัวเลขเวทมนตร์
            vector = get_embedding(text_to_embed)

            doc = {
                "source_file": filename,
                "type": item_type,
                "name": item_name,
                "value": numeric_value,
                "content": text_to_embed,
                "embedding": vector
            }
            doc.update(extra_data)
            documents.append(doc)

            if len(documents) >= 50:
                collection.insert_many(documents)
                documents = []
                print(f"อัปโหลดแล้ว {index + 1} รายการ จากไฟล์ {filename}")

        # เก็บตกพวกที่เหลือไม่ถึง 50 ชิ้น
        if documents:
            collection.insert_many(documents)
            documents = []
    
    print("ดันข้อมูลขึ้น MongoDB เสร็จสิ้น! หล่อๆ เลยจารย์!")

if __name__ == "__main__":
    upload_to_mongo()