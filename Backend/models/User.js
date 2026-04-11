const mongoose = require("mongoose");

const userSchema = new mongoose.Schema(
  {
    email: {
      type: String,
      required: true,
      unique: true,
      trim: true,
      lowercase: true,
    },
    password: { type: String, required: true },
    isVerified: { type: Boolean, default: false },
    name: { type: String },

    // 🟢 ส่วนที่เพิ่มเข้ามาสำหรับการยืนยันอีเมลตอนสมัคร
    verificationCode: { type: String }, // เก็บเลข OTP 6 หลัก
    verificationCodeExpires: { type: Date }, // เวลาหมดอายุของเลขยืนยัน

    gender: {
      type: String,
      enum: ["male", "female", "other", "none"],
      default: "none",
    },
    birthDate: { type: Date },
    age: { type: Number },
    weight: { type: Number },
    height: { type: Number },
    dietaryPreference: { type: String, default: "none" },
    foodAllergies: [{ type: String }],
    avatar: { type: String, default: "" },

    // ส่วนของ Forgot Password เดิมของมึง
    resetCode: { type: String },
    resetCodeExpires: { type: Date },
  },

  { timestamps: true }
);

module.exports = mongoose.model("User", userSchema);