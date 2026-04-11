const User = require('../models/User'); 

// อัปเดตข้อมูลสุขภาพและรูปโปรไฟล์ผู้ใช้
exports.updateProfile = async (req, res) => {
  try {
    const userId = req.user.id; 
    
    // 🟢 1. รับ gender กับ birthDate มาด้วยเว้ย!
    const { weight, height, dietaryPreference, foodAllergies, avatar, gender, birthDate } = req.body;

    // 🟢 2. ระบบคำนวณอายุอัตโนมัติจากวันเกิด
    let calculatedAge = undefined;
    if (birthDate) {
      const birth = new Date(birthDate);
      const today = new Date();
      calculatedAge = today.getFullYear() - birth.getFullYear();
      const m = today.getMonth() - birth.getMonth();
      // ถ้าย้อนกลับไปเดือนเกิดแล้วยังไม่ถึง หรือเดือนเดียวกันแต่วันยังไม่ถึง ให้ลบอายุไป 1 ปี
      if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) {
        calculatedAge--;
      }
    }

    const updatedUser = await User.findByIdAndUpdate(
      userId,
      { 
        weight, 
        height, 
        dietaryPreference, 
        foodAllergies, 
        avatar,
        gender,       // 🟢 3. ยัดเพศลง DB
        birthDate,    // 🟢 4. ยัดวันเกิดลง DB
        age: calculatedAge // 🟢 5. ยัดอายุที่คำนวณได้ลง DB
      },
      { new: true, runValidators: true } 
    ).select('-password'); 

    if (!updatedUser) {
      return res.status(404).json({ message: 'หาผู้ใช้ไม่เจอ' });
    }

    return res.status(200).json({ 
      message: 'อัปเดตโปรไฟล์เรียบร้อย', 
      user: updatedUser 
    });

  } catch (error) {
    console.error("Update Profile Error:", error);
    return res.status(500).json({ message: 'เซิร์ฟเวอร์มีปัญหาตอนบันทึกข้อมูล' });
  }
};


exports.getProfile = async (req, res) => {
  try {
    const user = await User.findById(req.user.id).select('-password');
    if (!user) return res.status(404).json({ message: 'ไม่เจอผู้ใช้' });
    res.status(200).json(user);
  } catch (error) {
    res.status(500).json({ message: 'ดึงข้อมูลไม่สำเร็จ' });
  }
};