const axios = require('axios');
const User = require('../models/User'); // ดึง Model User มาเพื่อดึงข้อมูลโปรไฟล์

exports.chatWithAI = async (req, res) => {
    try {
        // 1. รับข้อความและประวัติแชทจาก Frontend (React)
        const { message, chat_history } = req.body;
        
        // 2. ดึงข้อมูล Profile ของ User จาก Database เราเอง
        // สมมติว่า req.user.id มาจาก authMiddleware ที่มึงล็อกอินไว้
        const userId = req.user.id; 
        const userProfile = await User.findById(userId);

        if (!userProfile) {
            return res.status(404).json({ error: "ไม่พบข้อมูลผู้ใช้งาน" });
        }

        // 3. แพ็กของใส่กล่องให้ตรงกับโครงสร้างที่ Python (app.py) ต้องการเป๊ะๆ
        const payload = {
            message: message,
            user: {
                name: userProfile.name || "ผู้ใช้งาน",
                weight: userProfile.weight || 0,
                height: userProfile.height || 0,
                age: userProfile.age || 0,
                gender: userProfile.gender || "unknown",
                dietaryPreference: userProfile.dietaryPreference || "",
                foodAllergies: userProfile.foodAllergies || []
            },
            chat_history: chat_history || []
        };

        // 4. สั่ง Node.js ยิง Request ข้ามไปหา Python FastAPI (ที่รันอยู่พอร์ต 8000)
        console.log("ส่งข้อมูลไปให้ Python คิด...");
        const pythonResponse = await axios.post('http://127.0.0.1:8000/api/chat', payload);

        // 5. รับคำตอบที่ Python คิดเสร็จ ส่งกลับไปโชว์ที่หน้าเว็บ React
        return res.status(200).json(pythonResponse.data);

    } catch (error) {
        console.error("❌ Python AI Error:", error.message);
        return res.status(500).json({ error: "สมอง AI ขัดข้องชั่วคราว ลองใหม่อีกครั้งนะจารย์" });
    }
};