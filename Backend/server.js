require('dotenv').config();
const express = require('express');
const cors = require('cors');
const connectDB = require('./config/db');
const { connectCloudinary } = require('./config/cloudinary')
// นำเข้า Routes สำหรับระบบสมาชิก
const authRoutes = require('./routes/authRoutes');
const profileRoutes = require('./routes/profileRoutes');
const chatRoutes = require('./routes/chatRoutes');
const app = express();


connectCloudinary();
// เชื่อมต่อฐานข้อมูล
connectDB();

// ตั้งค่า Middleware
app.use(cors({
  origin: "http://localhost:5174",
  methods: ["GET", "POST", "PUT", "DELETE"],
  credentials: true
}));


app.use(express.json()); 

// ตั้งค่า Routes หลัก
app.use('/api/auth', authRoutes);
app.use('/api/profile', profileRoutes);


app.use('/api/chat', chatRoutes);


// Route พื้นฐานสำหรับทดสอบการทำงานของเซิร์ฟเวอร์
app.get('/', (req, res) => {
  res.send('API is running...');
});

// กำหนดพอร์ตและเริ่มรันเซิร์ฟเวอร์
const PORT = process.env.PORT || 5000;

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});