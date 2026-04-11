const User = require('../models/User');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const nodemailer = require('nodemailer');

// 1. ตรวจสอบอีเมล
exports.checkEmail = async (req, res) => {
  try {
    const { email } = req.body;
    const user = await User.findOne({ email });
    return res.status(200).json({ exists: !!user });
  } catch (error) {
    console.error("Check Email Error:", error);
    return res.status(500).json({ message: 'เกิดข้อผิดพลาดในการตรวจสอบข้อมูล' });
  }
};

// 2. สมัครสมาชิก
exports.register = async (req, res) => {
  try {
    const { email, password, name } = req.body;
    const existingUser = await User.findOne({ email });
    if (existingUser) return res.status(400).json({ message: 'อีเมลนี้มีในระบบแล้ว' });

    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(password, salt);

    const code = Math.floor(100000 + Math.random() * 900000).toString();

    const newUser = new User({
      name,
      email,
      password: hashedPassword,
      isVerified: false,
      verificationCode: code,
      verificationCodeExpires: new Date(Date.now() + 24 * 60 * 60 * 1000)
    });

    await newUser.save();

    // 🟢 1. ต้องใส่ตั้งค่า transporter ให้ครบแบบนี้จารย์!
    const transporter = nodemailer.createTransport({
      host: 'smtp.gmail.com',
      port: 587,
      secure: false,
      auth: {
        user: process.env.EMAIL_USER,
        pass: process.env.EMAIL_PASS
      }
    });

    // 🟢 2. ส่งเมลจริง (ใช้ Template สวยๆ)
    await transporter.sendMail({
      from: `"ChatBot Support" <${process.env.EMAIL_USER}>`,
      to: email,
      subject: 'ยืนยันอีเมลของมึงหน่อยจารย์!',
      html: `
        <div style="font-family: Arial, sans-serif; border: 1px solid #eee; padding: 20px; border-radius: 10px;">
          <h2 style="color: #10b981;">ยินดีต้อนรับสู่ ChatBot ของเรา</h2>
          <p>ยืนยันอีเมลของคุณเพื่อเข้าสู่ระบบ</p>
          <div style="background: #f3f4f6; padding: 15px; text-align: center; font-size: 30px; font-weight: bold; color: #10b981; letter-spacing: 5px;">
            ${code}
          </div>
        </div>
      `
    });

    return res.status(201).json({ message: 'สร้างบัญชีแล้ว เช็คเมลเพื่อเอารหัสมายืนยันนะ' });
  } catch (error) {
    // 🟢 3. ต้องมีบรรทัดนี้! มึงจะได้เห็นใน Terminal ว่ามันตายเพราะอะไร (เช่น ลืมลง Lib หรือรหัสเมลผิด)
    console.error("Register Error Details:", error); 
    res.status(500).json({ message: 'something went wrong' });
  }
};

// 3. เข้าสู่ระบบ
exports.login = async (req, res) => {
  try {
    const { email, password } = req.body;
    const user = await User.findOne({ email });
    if (!user) return res.status(400).json({ message: 'ไม่พบข้อมูลผู้ใช้งาน' });

    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return res.status(400).json({ message: 'รหัสผ่านไม่ถูกต้อง' });

    const token = jwt.sign({ id: user._id }, process.env.JWT_SECRET, { expiresIn: '1d' });

    return res.status(200).json({
      message: 'เข้าสู่ระบบสำเร็จ',
      token,
      user: {
        id: user._id,
        name: user.name,
        email: user.email,
        weight: user.weight,
        height: user.height,
        avatar: user.avatar,
        gender: user.gender,
        birthDate: user.birthDate,
        age: user.age
      }
    });
  } catch (error) {
    console.error("Login Error:", error);
    return res.status(500).json({ message: 'เกิดข้อผิดพลาดในการเข้าสู่ระบบ' });
  }
};

// 4. อัปเดตโปรไฟล์
exports.updateProfile = async (req, res) => {
  try {
    const { weight, height, dietaryPreference, foodAllergies, gender, birthDate, avatar } = req.body;
    
    let calculatedAge = null;
    if (birthDate) {
      const birth = new Date(birthDate);
      const today = new Date();
      calculatedAge = today.getFullYear() - birth.getFullYear();
      const m = today.getMonth() - birth.getMonth();
      if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) {
        calculatedAge--;
      }
    }

    const user = await User.findByIdAndUpdate(
      req.user.id,
      { 
        weight, height, dietaryPreference, foodAllergies, gender, birthDate, 
        age: calculatedAge,
        ...(avatar && { avatar }) 
      },
      { new: true } 
    );

    if (!user) return res.status(404).json({ message: 'ไม่พบผู้ใช้งาน' });
    return res.status(200).json({ message: 'อัปเดตข้อมูลสำเร็จ', user });
  } catch (error) {
    console.error("Update Profile Error:", error);
    return res.status(500).json({ message: 'เกิดข้อผิดพลาดในการอัปเดตข้อมูล' });
  }
};

// 5. เปลี่ยนรหัสผ่าน (แบบล็อกอินอยู่)
exports.changePassword = async (req, res) => {
  try {
    const { currentPassword, newPassword } = req.body;
    const user = await User.findById(req.user.id);
    
    const isMatch = await bcrypt.compare(currentPassword, user.password);
    if (!isMatch) return res.status(400).json({ message: 'รหัสผ่านปัจจุบันไม่ถูกต้อง' });

    const salt = await bcrypt.genSalt(10);
    user.password = await bcrypt.hash(newPassword, salt);
    await user.save();

    return res.status(200).json({ message: 'เปลี่ยนรหัสผ่านสำเร็จ' });
  } catch (error) {
    console.error("Change Password Error:", error);
    return res.status(500).json({ message: 'something went wrong' });
  }
};

// 6. ลืมรหัสผ่าน (ส่งเมล)
exports.forgotPassword = async (req, res) => {
  try {
    const { email } = req.body;
    const user = await User.findOne({ email });
    if (!user) return res.status(404).json({ message: 'Email not found' });

    // สร้าง Code 6 หลัก
    const code = Math.floor(100000 + Math.random() * 900000).toString();
    
    // เซฟลง DB และใช้ new Date() เพื่อแก้ปัญหาวันหมดอายุเอ๋อ
    user.resetCode = code;
    user.resetCodeExpires = new Date(Date.now() + 10 * 60 * 1000); 
    await user.save();

    const transporter = nodemailer.createTransport({
      host: 'smtp.gmail.com',
      port: 587,
      secure: false,
      auth: {
        user: process.env.EMAIL_USER,
        pass: process.env.EMAIL_PASS
      }
    });

    // 🟢 ส่งเมลแบบ HTML สวยๆ
    await transporter.sendMail({
      from: `"ChatBot Support" <${process.env.EMAIL_USER}>`,
      to: email,
      subject: 'รหัสยืนยันการเปลี่ยนรหัสผ่าน (Reset Password)',
      html: `
        <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px; background-color: #ffffff;">
          <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #2563eb; margin: 0;">VERIFY CODE</h2>
          </div>
          <p style="color: #4b5563; text-align: center; font-size: 16px;">ห้ามแชร์รหัสให้ผู้อื่นเพื่อความปลอดภัยของดาวอังคาร</p>
          <div style="background-color: #f8fafc; border: 2px dashed #cbd5e1; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px;">
            <span style="font-size: 32px; font-weight: bold; color: #2563eb; letter-spacing: 0.2em;">${code}</span>
          </div>
          <p style="color: #9ca3af; font-size: 12px; text-align: center;">รหัสนี้มีอายุ 10 นาทีเท่านั้นถ้าไม่ได้ทำรายการเองก็น่าจะมีคนทำแทน</p>
        </div>
      `
    });

    return res.status(200).json({ message: 'ส่ง Code เรียบร้อย!' });
  } catch (error) {
    console.error("Forgot Password Error:", error); 
    return res.status(500).json({ message: 'something went wrong' });
  }
};

// 7. ตรวจสอบ Code
exports.verifyCode = async (req, res) => {
  try {
    const { email, code } = req.body;
    const user = await User.findOne({ 
      email, 
      resetCode: code, 
      resetCodeExpires: { $gt: new Date() } // 🟢 ใช้ $gt เปรียบเทียบกับ new Date()
    });

    if (!user) return res.status(400).json({ message: 'Your code is not valid' });
    return res.status(200).json({ message: 'ตรวจสอบรหัสสําเร็จ' });
  } catch (error) {
    console.error("Verify Code Error:", error);
    return res.status(500).json({ message: 'something went wrong' });
  }
};

// 8. รีเซ็ตรหัสผ่านใหม่
exports.resetPassword = async (req, res) => {
  try {
    const { email, newPassword } = req.body;
    const user = await User.findOne({ email });
    if (!user) return res.status(404).json({ message: 'ไม่พบผู้ใช้งาน' });

    const salt = await bcrypt.genSalt(10);
    user.password = await bcrypt.hash(newPassword, salt);
    
    // ล้าง Code ทิ้ง
    user.resetCode = undefined;
    user.resetCodeExpires = undefined;
    await user.save();

    return res.status(200).json({ message: 'เปลี่ยนรหัสสำเร็จ!' });
  } catch (error) {
    console.error("Reset Password Error:", error);
    return res.status(500).json({ message: 'เปลี่ยนรหัสไม่สำเร็จ' });
  }
};

exports.verifyEmail = async (req, res) => {
  try {
    const { email, code } = req.body;
    const user = await User.findOne({ 
      email, 
      verificationCode: code,
      verificationCodeExpires: { $gt: new Date() }
    });

    if (!user) return res.status(400).json({ message: 'รหัสผิดหรือหมดอายุแล้ว' });

    user.isVerified = true;
    user.verificationCode = undefined;
    user.verificationCodeExpires = undefined;
    await user.save();

    // 🟢 พอยืนยันเสร็จ ค่อยเจน Token ให้มันล็อกอินเข้าแอปได้จริง
    const token = jwt.sign({ id: user._id }, process.env.JWT_SECRET, { expiresIn: '1d' });

    res.status(200).json({ message: 'ยืนยันอีเมลสำเร็จ!', token, user });
  } catch (error) {
    res.status(500).json({ message: 'something went wrong' });
  }
};