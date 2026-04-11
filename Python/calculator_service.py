# calculator_service.py

def calculate_bmr(weight, height, age, gender):
    # เป้าหมาย: คำนวณ BMR (Basal Metabolic Rate) พลังงานพื้นฐานตอนอยู่เฉยๆ
    base_bmr = (10 * weight) + (6.25 * height) - (5 * age)
    
    if gender.lower() in ['male', 'm', 'ชาย']:
        return round(base_bmr + 5, 2)
    elif gender.lower() in ['female', 'f', 'หญิง']:
        return round(base_bmr - 161, 2)
    else:
        # ถ้าไม่ระบุเพศ ใช้ค่าเฉลี่ยกลางๆ
        return round(base_bmr - 78, 2)

def calculate_bmi(weight_kg, height_cm):
    # เป้าหมาย: คำนวณดัชนีมวลกาย (BMI) ให้บอทรู้ว่าอ้วนหรือผอม
    if height_cm <= 0:
        return 0
    height_m = height_cm / 100.0
    bmi = weight_kg / (height_m ** 2)
    return round(bmi, 2)

def calculate_tdee(bmr, activity_level="sedentary"):
    # เป้าหมาย: คำนวณ TDEE (Total Daily Energy Expenditure) พลังงานที่ใช้จริงทั้งวัน
    # ระดับการทำกิจกรรม:
    # sedentary = นั่งทำงานเฉยๆ ไม่ค่อยออกกำลัง (1.2)
    # lightly_active = ออกกำลังกายเบาๆ 1-3 วัน/สัปดาห์ (1.375)
    # moderately_active = ออกกำลังกายปานกลาง 3-5 วัน/สัปดาห์ (1.55)
    # very_active = ออกกำลังกายหนัก 6-7 วัน/สัปดาห์ (1.725)
    # extra_active = นักกีฬา ทำงานใช้แรงงานหนักมาก (1.9)
    
    factors = {
        "sedentary": 1.2,
        "lightly_active": 1.375,
        "moderately_active": 1.55,
        "very_active": 1.725,
        "extra_active": 1.9
    }
    
    multiplier = factors.get(activity_level.lower(), 1.2) # ค่า Default คือขี้เกียจนั่งเฉยๆ
    return round(bmr * multiplier, 2)

def calculate_calories_burned(met_value, weight_kg, duration_minutes):
    # เป้าหมาย: คำนวณแคลอรีที่เผาผลาญจากการออกกำลังกายแต่ละท่า
    duration_hours = duration_minutes / 60.0
    burned = met_value * weight_kg * duration_hours
    return round(burned, 2)

if __name__ == "__main__":
    # 🟢 เทสต์ระบบแบบจัดเต็ม!
    user_weight = 70
    user_height = 175
    user_age = 25
    user_gender = "male"
    
    bmr = calculate_bmr(user_weight, user_height, user_age, user_gender)
    bmi = calculate_bmi(user_weight, user_height)
    tdee = calculate_tdee(bmr, "moderately_active")
    
    print(f"--- สรุปร่างกาย ---")
    print(f"BMI: {bmi}")
    print(f"BMR (นอนเฉยๆ): {bmr} kcal")
    print(f"TDEE (เผาผลาญทั้งวัน): {tdee} kcal")
    
    met = 4.0 # เดินเร็ว
    time_min = 30
    burned = calculate_calories_burned(met, user_weight, time_min)
    print(f"\n--- ออกกำลังกาย ---")
    print(f"ยูสเซอร์เดินเร็ว {time_min} นาที เผาผลาญไปเพิ่มอีก: {burned} kcal")