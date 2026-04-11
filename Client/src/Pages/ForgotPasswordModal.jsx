import React, { useState } from 'react';
import axios from 'axios';
import Swal from 'sweetalert2';
import { FaEnvelope, FaLock, FaKey, FaTimes } from 'react-icons/fa';

function ForgotPasswordModal({ isOpen, onClose }) {
  const [step, setStep] = useState(1); // 1: กรอกเมล, 2: กรอก Code + รหัสใหม่
  const [email, setEmail] = useState('');
  const [data, setData] = useState({ code: '', newPassword: '', confirmPassword: '' });
  const [isLoading, setIsLoading] = useState(false);

  if (!isOpen) return null;

  // 1. ยิงเมลเพื่อขอ Code
  const handleRequestCode = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await axios.post('http://localhost:5000/api/auth/forgot-password', { email });
      Swal.fire({ icon: 'success', title: 'ส่ง Code แล้ว!', text: 'เช็ครหัสในอีเมล รหัสมีอายุ 10 นาที', timer: 2000 });
      setStep(2); // ไปสเตปถัดไป
    } catch (err) {
      Swal.fire({ icon: 'error', title: 'ว้ายย พลาด!', text: err.response?.data?.message || 'ส่งไม่สำเร็จ' });
    } finally {
      setIsLoading(false);
    }
  };

  // 2. ยืนยัน Code และ Reset Password
  const handleResetPassword = async (e) => {
    e.preventDefault();
    if (data.newPassword !== data.confirmPassword) return Swal.fire({ icon: 'warning', text: 'รหัสใหม่ไม่ตรงกัน' });

    setIsLoading(true);
    try {
      await axios.post('http://localhost:5000/api/auth/reset-password', {
        email,
        code: data.code,
        newPassword: data.newPassword
      });
      await Swal.fire({ icon: 'success', title: 'เรียบร้อย!', text: 'เปลี่ยนรหัสผ่านใหม่แล้ว เข้าสู่ระบบได้เลย' });
      onClose(); // ปิด Modal
      setStep(1); // รีเซ็ตสเตป
    } catch (err) {
      Swal.fire({ icon: 'error', title: 'พัง', text: err.response?.data?.message || 'Reset ไม่สำเร็จ' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[150] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-300">
      <div className="bg-white w-full max-w-md rounded-2xl shadow-2xl overflow-hidden relative animate-in zoom-in-95 duration-300">
        
        {/* ปุ่มปิด */}
        <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors">
          <FaTimes />
        </button>

        <div className="p-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-2">
            {step === 1 ? 'ลืมรหัสผ่าน' : 'ยืนยันรหัส'}
          </h2>
          <p className="text-sm text-gray-500 mb-8">
            {step === 1 ? 'ใส่เมลมา เดี๋ยวส่ง Code 6 หลักไปให้' : `ส่งรหัสไปที่ ${email} แล้ว`}
          </p>

          {step === 1 ? (
            /* 🟢 Step 1: กรอก Email */
            <form onSubmit={handleRequestCode} className="space-y-5">
              <div className="relative">
                <FaEnvelope className="absolute top-4 left-4 text-gray-400" />
                <input 
                  type="email" required placeholder="Email "
                  value={email} onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 transition-all"
                />
              </div>
              <button 
                type="submit" disabled={isLoading}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-xl transition-all shadow-lg shadow-blue-600/20 active:scale-95 disabled:opacity-50"
              >
                {isLoading ? 'กำลังส่ง...' : 'ขอรหัสยืนยัน'}
              </button>
            </form>
          ) : (
            /* 🟢 Step 2: กรอก Code + Password ใหม่ */
            <form onSubmit={handleResetPassword} className="space-y-4">
              <div className="relative">
                <FaKey className="absolute top-4 left-4 text-gray-400" />
                <input 
                  type="text" required placeholder="รหัส 6 หลักจากเมล"
                  value={data.code} onChange={(e) => setData({...data, code: e.target.value})}
                  className="w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl outline-none focus:border-blue-600 transition-all text-center tracking-[0.5em] font-bold"
                  maxLength="6"
                />
              </div>
              <div className="relative">
                <FaLock className="absolute top-4 left-4 text-gray-400" />
                <input 
                  type="password" required placeholder="รหัสผ่านใหม่"
                  value={data.newPassword} onChange={(e) => setData({...data, newPassword: e.target.value})}
                  className="w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl outline-none focus:border-blue-600 transition-all"
                />
              </div>
              <div className="relative">
                <FaLock className="absolute top-4 left-4 text-gray-400" />
                <input 
                  type="password" required placeholder="ยืนยันรหัสผ่านใหม่"
                  value={data.confirmPassword} onChange={(e) => setData({...data, confirmPassword: e.target.value})}
                  className="w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl outline-none focus:border-blue-600 transition-all"
                />
              </div>
              <button 
                type="submit" disabled={isLoading}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-xl transition-all shadow-lg shadow-blue-600/20 active:scale-95 disabled:opacity-50"
              >
                {isLoading ? 'กำลังบันทึก...' : 'เปลี่ยนรหัสผ่านเลย'}
              </button>
              <button type="button" onClick={() => setStep(1)} className="w-full text-xs text-gray-400 hover:text-gray-600 transition-colors">ย้อนกลับไปกรอกเมลใหม่</button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

export default ForgotPasswordModal;