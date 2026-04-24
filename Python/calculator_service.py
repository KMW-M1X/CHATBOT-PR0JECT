import math

def calculate_bmi(weight_kg, height_cm):
    # เป้าหมาย: คำนวณดัชนีมวลกาย (BMI) เพื่อประเมินสภาวะร่างกาย
    if not weight_kg or not height_cm or height_cm <= 0:
        return 0
    height_m = height_cm / 100.0
    bmi = weight_kg / (height_m ** 2)
    return round(bmi, 2)

def calculate_bmr(weight, height, age, gender):
    # เป้าหมาย: คำนวณอัตราการเผาผลาญพลังงานพื้นฐาน (BMR) ตามสูตร Mifflin-St Jeor
    if not all([weight, height, age]) or age <= 0:
        return 0
        
    base_bmr = (10 * weight) + (6.25 * height) - (5 * age)
    
    # แยกตามเพศเพื่อความแม่นยำ
    if gender.lower() in ['male', 'm', 'ชาย']:
        return round(base_bmr + 5, 2)
    elif gender.lower() in ['female', 'f', 'หญิง']:
        return round(base_bmr - 161, 2)
    else:
        # กรณีระบุเพศไม่ชัดเจน ใช้ค่าเฉลี่ยกลาง
        return round(base_bmr - 78, 2)

def calculate_tdee(bmr, activity_level="sedentary"):
    # เป้าหมาย: คำนวณพลังงานที่ใช้จริงต่อวัน (TDEE) ตามระดับกิจกรรม
    if not bmr or bmr <= 0:
        return 0
        
    factors = {
        "sedentary": 1.2,               # นั่งทำงานเฉยๆ
        "lightly_active": 1.375,        # ออกกำลังเบาๆ 1-3 วัน/สัปดาห์
        "moderately_active": 1.55,      # ออกกำลังปานกลาง 3-5 วัน/สัปดาห์
        "very_active": 1.725,           # ออกกำลังหนัก 6-7 วัน/สัปดาห์
        "extra_active": 1.9             # ทำงานใช้แรงงานหนักมาก/นักกีฬา
    }
    
    multiplier = factors.get(activity_level.lower(), 1.2)
    return round(bmr * multiplier, 2)

def calculate_calories_burned(met_value, weight_kg, duration_minutes):
    # เป้าหมาย: คำนวณแคลอรีที่เผาผลาญจากการทำกิจกรรมตามค่า METs
    if not all([met_value, weight_kg, duration_minutes]) or duration_minutes <= 0:
        return 0
        
    duration_hours = duration_minutes / 60.0
    burned = met_value * weight_kg * duration_hours
    return round(burned, 2)

def get_bmi_category(bmi):
    # เป้าหมาย: จัดกลุ่มเกณฑ์ BMI เพื่อให้คำแนะนำเบื้องต้น
    if bmi <= 0: return "ไม่ทราบข้อมูล"
    if bmi < 18.5: return "น้ำหนักน้อย / ผอม"
    elif 18.5 <= bmi < 23: return "ปกติ (สุขภาพดี)"
    elif 23 <= bmi < 25: return "ท้วม / โรคอ้วนระดับ 1"
    elif 25 <= bmi < 30: return "อ้วน / โรคอ้วนระดับ 2"
    else: return "อ้วนมาก / โรคอ้วนระดับ 3"

if __name__ == "__main__":
    # 🟢 ส่วนทดสอบระบบ (Test Suite)
    test_w, test_h, test_a = 75, 180, 28
    test_g = "male"
    
    bmi = calculate_bmi(test_w, test_h)
    bmr = calculate_bmr(test_w, test_h, test_a, test_g)
    tdee = calculate_tdee(bmr, "moderately_active")
    
    print(f"=== ผลการทดสอบส ===")
    print(f"BMI: {bmi} ({get_bmi_category(bmi)})")
    print(f"BMR: {bmr} kcal/day")
    print(f"TDEE: {tdee} kcal/day")
    
    # ทดสอบคำนวณการวิ่ง (สมมติ MET = 8.0)
    burned = calculate_calories_burned(8.0, test_w, 45)
    print(f"วิ่ง 45 นาที เผาผลาญไป: {burned} kcal")