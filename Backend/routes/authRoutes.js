// routes/authRoutes.js
const express = require('express');
const router = express.Router();
const authController = require('../controllers/authController');
const { changePassword } = require('../controllers/authController');
const { forgotPassword } = require('../controllers/authController');
const authMiddleware = require('../middlewares/authMiddleware'); 
const {resetPassword} = require('../controllers/authController');
const {verifyEmail} = require('../controllers/authController');

router.post('/check-email', authController.checkEmail);
router.post('/register', authController.register);
router.post('/login', authController.login);
router.put('/change-password', authMiddleware, changePassword);
router.post('/forgot-password', forgotPassword);
router.post('/reset-password', authController.resetPassword);

router.post('/verify-email', authController.verifyEmail);
// 🟢 เพิ่ม Route นี้เข้าไป (ต้องผ่านการเช็ค Token ก่อนถึงจะอัปเดตได้)
router.put('/update-profile', authMiddleware, authController.updateProfile);

module.exports = router;