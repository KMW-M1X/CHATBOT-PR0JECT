import React, { useState } from 'react';
import axios from 'axios';
import Swal from 'sweetalert2'; 

function AuthModal({ isOpen, onClose, onLoginSuccess }) {
  const [step, setStep] = useState('email'); 
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  const [code, setCode] = useState(''); 
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const API_URL = 'http://localhost:5000/api/auth'; 

  const Toast = Swal.mixin({
    toast: true,
    position: 'top-end',
    showConfirmButton: false,
    timer: 2000,
    background: '#131314',
    color: '#ffffff'
  });

  if (!isOpen) return null;

  const handleCheckEmail = async (e) => {
    e.preventDefault();
    if (!email) return;
    setIsLoading(true);
    setErrorMessage('');
    try {
      const response = await axios.post(`${API_URL}/check-email`, { email });
      if (response.data.exists) setStep('login');
      else setStep('register');
    } catch (error) {
      setErrorMessage('เซิร์ฟเวอร์มีปัญหา ลองใหม่');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage('');
    try {
      const response = await axios.post(`${API_URL}/login`, { email, password });
      if (response.data.token) localStorage.setItem('token', response.data.token);
      Toast.fire({ icon: 'success', title: 'เข้าสู่ระบบสำเร็จ' });
      if (onLoginSuccess) onLoginSuccess(response.data.user);
      handleClose();
    } catch (error) {
      const msg = error.response?.data?.message || 'ข้อมูลไม่ถูกต้อง';
      if (msg.includes('ยืนยันเมล')) setStep('verify-reg');
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    if (password !== confirmPassword) {
      setErrorMessage('รหัสผ่านไม่ตรงกัน');
      return;
    }
    setIsLoading(true);
    try {
      await axios.post(`${API_URL}/register`, { email, password, name });
      Toast.fire({ icon: 'info', title: 'ส่งรหัสยืนยันแล้ว' });
      setStep('verify-reg');
    } catch (error) {
      setErrorMessage(error.response?.data?.message || 'สมัครไม่สำเร็จ');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyRegSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const response = await axios.post(`${API_URL}/verify-email`, { email, code });
      if (response.data.token) localStorage.setItem('token', response.data.token);
      await Swal.fire({ icon: 'success', title: 'ยืนยันตัวตนสำเร็จ', background: '#131314', color: '#ffffff' });
      if (onLoginSuccess) onLoginSuccess(response.data.user);
      handleClose();
    } catch (error) {
      setErrorMessage(error.response?.data?.message || 'รหัสไม่ถูกต้อง');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRequestReset = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage('');
    try {
      await axios.post(`${API_URL}/forgot-password`, { email });
      Toast.fire({ icon: 'success', title: 'ส่งรหัสกู้คืนแล้ว' });
      setStep('reset');
    } catch (error) {
      setErrorMessage(error.response?.data?.message || 'ส่งอีเมลไม่สำเร็จ');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetSubmit = async (e) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setErrorMessage('รหัสใหม่ไม่ตรงกัน');
      return;
    }
    setIsLoading(true);
    try {
      await axios.post(`${API_URL}/reset-password`, { email, code, newPassword: password });
      await Swal.fire({ icon: 'success', title: 'สำเร็จ', text: 'เปลี่ยนรหัสผ่านแล้ว', background: '#131314', color: '#ffffff' });
      setStep('login');
      setPassword('');
      setConfirmPassword('');
    } catch (error) {
      setErrorMessage(error.response?.data?.message || 'รหัสผิดหรือหมดอายุ');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setStep('email'); setEmail(''); setPassword(''); setConfirmPassword(''); setName(''); setCode(''); setErrorMessage('');
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-lg p-4">
      <div className="relative w-full max-w-[450px] bg-[#131314]/95 rounded-2xl border border-white/10 p-8 shadow-2xl">
        
        <button onClick={handleClose} className="absolute top-4 right-4 text-gray-500 hover:text-white transition-colors">
          <span className="material-symbols-outlined">close</span>
        </button>

        <div className="flex flex-col items-center">
          <div className="w-14 h-14 bg-white/5 rounded-xl flex items-center justify-center mb-6">
             <span className="material-symbols-outlined text-gray-300" style={{ fontSize: '28px' }}>
               {['reset', 'forgot', 'verify-reg'].includes(step) ? 'lock' : 'person'}
             </span>
          </div>

          {errorMessage && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/50 text-red-400 rounded-lg text-xs text-center w-full">
              {errorMessage}
            </div>
          )}
          
          {step === 'email' && (
            <div className="w-full text-center">
              <h2 className="text-xl font-bold text-white mb-6">ระบุอีเมล</h2>
              <form onSubmit={handleCheckEmail} className="space-y-4">
                <input type="email" required placeholder="อีเมล" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full bg-white/5 text-white border border-white/10 rounded-lg px-4 py-3 outline-none focus:border-blue-500" />
                <button type="submit" disabled={isLoading} className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg py-3 transition-all">
                   {isLoading ? 'กำลังโหลด...' : 'ต่อไป'}
                </button>
              </form>
            </div>
          )}

          {step === 'login' && (
            <div className="w-full text-center">
              <h2 className="text-xl font-bold text-white mb-1">เข้าสู่ระบบ</h2>
              <p className="text-gray-500 text-xs mb-6">{email}</p>
              <form onSubmit={handleLoginSubmit} className="space-y-4">
                <input type="password" required placeholder="รหัสผ่าน" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full bg-white/5 text-white border border-white/10 rounded-lg px-4 py-3 outline-none focus:border-blue-500" />
                <button type="submit" disabled={isLoading} className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg py-3">เข้าสู่ระบบ</button>
              </form>
              <div className="mt-6 flex justify-between px-2">
                <button onClick={() => setStep('forgot')} className="text-xs text-gray-500 hover:text-blue-400">ลืมรหัสผ่าน?</button>
                <button onClick={() => setStep('email')} className="text-xs text-gray-500 hover:text-white">เปลี่ยนอีเมล</button>
              </div>
            </div>
          )}

          {step === 'register' && (
            <div className="w-full text-center">
              <h2 className="text-xl font-bold text-white mb-6">สมัครสมาชิก</h2>
              <form onSubmit={handleRegisterSubmit} className="space-y-3">
                <input type="text" required placeholder="ชื่อที่อยากให้บอทเรียก" value={name} onChange={(e) => setName(e.target.value)} className="w-full bg-white/5 text-white border border-white/10 rounded-lg px-4 py-3 outline-none focus:border-emerald-500" />
                <input type="password" required placeholder="รหัสผ่าน" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full bg-white/5 text-white border border-white/10 rounded-lg px-4 py-3 outline-none focus:border-emerald-500" />
                <input type="password" required placeholder="ยืนยันรหัสผ่าน" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="w-full bg-white/5 text-white border border-white/10 rounded-lg px-4 py-3 outline-none focus:border-emerald-500" />
                <button type="submit" disabled={isLoading} className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-lg py-3">สมัคร</button>
              </form>
              <button onClick={() => setStep('email')} className="mt-4 text-xs text-gray-500 hover:text-white">ย้อนกลับ</button>
            </div>
          )}

          {step === 'verify-reg' && (
            <div className="w-full text-center">
              <h2 className="text-xl font-bold text-white mb-2">ยืนยันรหัส</h2>
              <p className="text-emerald-400 text-xs mb-6">รหัสส่งไปที่ {email}</p>
              <form onSubmit={handleVerifyRegSubmit} className="space-y-4">
                <input type="text" required placeholder="6 หลัก" maxLength="6" value={code} onChange={(e) => setCode(e.target.value)} className="w-full bg-white/5 text-white border border-white/10 rounded-lg px-4 py-3 text-center tracking-widest font-bold text-lg" />
                <button type="submit" disabled={isLoading} className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-lg py-3">ตกลง</button>
              </form>
            </div>
          )}

          {step === 'forgot' && (
            <div className="w-full text-center">
              <h2 className="text-xl font-bold text-white mb-6">กู้คืนรหัสผ่าน</h2>
              <p className="text-gray-500 text-xs mb-6">รหัสยืนยันจะถูกส่งไปที่ {email}</p>
              <form onSubmit={handleRequestReset} className="space-y-4">
                <button type="submit" disabled={isLoading} className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg py-3">ส่งรหัส</button>
              </form>
              <button onClick={() => setStep('login')} className="mt-4 text-xs text-gray-500 hover:text-white">ยกเลิก</button>
            </div>
          )}

          {step === 'reset' && (
            <div className="w-full text-center">
              <h2 className="text-xl font-bold text-white mb-6">ตั้งรหัสใหม่</h2>
              <form onSubmit={handleResetSubmit} className="space-y-4">
                <input type="text" required placeholder="รหัส 6 หลัก" maxLength="6" value={code} onChange={(e) => setCode(e.target.value)} className="w-full bg-white/5 text-white border border-white/10 rounded-lg px-4 py-3 text-center tracking-widest font-bold text-lg" />
                <input type="password" required placeholder="รหัสผ่านใหม่" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full bg-white/5 text-white border border-white/10 rounded-lg px-4 py-3" />
                <input type="password" required placeholder="ยืนยันรหัสใหม่" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="w-full bg-white/5 text-white border border-white/10 rounded-lg px-4 py-3" />
                <button type="submit" disabled={isLoading} className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg py-3">ยืนยัน</button>
              </form>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}

export default AuthModal;