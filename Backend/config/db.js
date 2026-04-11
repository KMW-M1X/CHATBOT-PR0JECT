const mongoose = require('mongoose');

// ฟังก์ชันเชื่อมต่อฐานข้อมูล MongoDB
const connectDB = async () => {
  try {
    const conn = await mongoose.connect(process.env.MONGO_URI);
    console.log(`MongoDB Connected: ${conn.connection.host}`);
  } catch (error) {
    console.error(`Error: ${error.message}`);
    // หยุดการทำงานของโปรเซสหากเชื่อมต่อฐานข้อมูลล้มเหลว
    process.exit(1); 
  }
};

module.exports = connectDB;