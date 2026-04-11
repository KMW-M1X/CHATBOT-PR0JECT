const jwt = require('jsonwebtoken');

// ตรวจสอบ Token เพื่ออนุญาตการเข้าถึง
const authMiddleware = (req, res, next) => {
  // รับ Token จาก Header
  const token = req.header('Authorization');

  // ตรวจสอบว่ามี Token ส่งมาหรือไม่
  if (!token) {
    return res.status(401).json({ message: 'ไม่มี Token ปฏิเสธการเข้าถึงข้อมูล' });
  }

  try {
    // ตัดคำว่า Bearer ออกและถอดรหัส
    const actualToken = token.startsWith('Bearer ') ? token.slice(7, token.length) : token;
    const decoded = jwt.verify(actualToken, process.env.JWT_SECRET);
    
    // แนบข้อมูลผู้ใช้ไปกับ request
    req.user = decoded;
    
    // ส่งต่อให้ทำงานถัดไป
    next();
  } catch (error) {
    console.error("JWT Verification Error:", error.message);
    return res.status(401).json({ message: 'Token ไม่ถูกต้อง หรือหมดอายุแล้ว' });
  }
};

module.exports = authMiddleware;