const express = require('express');
const router = express.Router();

const { updateProfile } = require('../controllers/profileController');
const { getProfile } = require('../controllers/profileController');
const authMiddleware = require('../middlewares/authMiddleware'); 


router.put('/update', authMiddleware, updateProfile);
router.get('/me', authMiddleware, getProfile); // เพิ่มบรรทัดนี้

module.exports = router;
