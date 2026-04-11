import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import Swal from 'sweetalert2';
import { FaCamera, FaRegUserCircle, FaLock, FaUser } from 'react-icons/fa';

import SettingsSidebar from '../Components/SettingsSidebar';
import SettingsNavbar from '../Components/SettingsNavbar';

function UserProfile() {
  const [user, setUser] = useState(null);
  const [editData, setEditData] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [isAvatarLoading, setIsAvatarLoading] = useState(false);
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [activeTab, setActiveTab] = useState('profile'); 
  
  const [passwordStep, setPasswordStep] = useState('normal'); 
  const [resetCode, setResetCode] = useState('');
  const [passwordData, setPasswordData] = useState({ currentPassword: '', newPassword: '', confirmPassword: '' });
  const [isPasswordLoading, setIsPasswordLoading] = useState(false);

  const calculateAge = (birthDate) => {
    if (!birthDate) return '--';
    const today = new Date();
    const birth = new Date(birthDate);
    let age = today.getFullYear() - birth.getFullYear();
    const m = today.getMonth() - birth.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
    return age > 0 ? age : 0;
  };

  const fetchProfile = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get('http://localhost:5000/api/profile/me', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(res.data);
      // 🟢 แปลง Array แพ้อาหาร ให้กลายเป็น String คั่นด้วยลูกน้ำ เพื่อเอามาโชว์ในช่องกรอก
      setEditData({
        ...res.data,
        foodAllergiesStr: res.data.foodAllergies ? res.data.foodAllergies.join(', ') : ''
      });
    } catch (err) {
      navigate('/');
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const handleAvatarUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsAvatarLoading(true);
    try {
      const cloudName = import.meta.env.VITE_CLOUDINARY_CLOUD_NAME; 
      const uploadPreset = import.meta.env.VITE_CLOUDINARY_UPLOAD_PRESET; 

      const formData = new FormData();
      formData.append('file', file);
      formData.append('upload_preset', uploadPreset);

      const cloudRes = await axios.post(`https://api.cloudinary.com/v1_1/${cloudName}/image/upload`, formData);
      const newAvatarUrl = cloudRes.data.secure_url;

      const token = localStorage.getItem('token');
      const res = await axios.put('http://localhost:5000/api/profile/update', 
        { avatar: newAvatarUrl },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setUser(res.data.user);
      Swal.fire({ toast: true, position: 'top-end', icon: 'success', title: 'อัปโหลดรูปเรียบร้อย!', showConfirmButton: false, timer: 1500 });
    } catch (error) {
      Swal.fire({ icon: 'error', title: 'Oops!', text: 'อัปโหลดรูปพลาดว่ะ' });
    } finally {
      setIsAvatarLoading(false);
    }
  };

  const handleDeleteAvatar = async () => {
    const result = await Swal.fire({
      title: 'ลบรูปโปรไฟล์?',
      text: "รูปจะหายไปเลยนะ!",
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#ef4444',
      confirmButtonText: 'ลบเลย!',
      cancelButtonText: 'ยกเลิก'
    });

    if (result.isConfirmed) {
      setIsAvatarLoading(true);
      try {
        const token = localStorage.getItem('token');
        const res = await axios.put('http://localhost:5000/api/profile/update', 
          { avatar: '' },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setUser(res.data.user);
        Swal.fire({ toast: true, position: 'top-end', icon: 'success', title: 'ลบรูปออกแล้ว', showConfirmButton: false, timer: 1500 });
      } catch (error) {
        Swal.fire({ icon: 'error', title: 'Error', text: 'ลบรูปไม่สำเร็จ' });
      } finally {
        setIsAvatarLoading(false);
      }
    }
  };

  const handleChange = (e) => {
    setEditData({ ...editData, [e.target.name]: e.target.value });
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const token = localStorage.getItem('token');
      
      // 🟢 แพ็กกล่องข้อมูลใหม่ หั่น String ลูกน้ำกลับไปเป็น Array ก่อนส่งไป Backend
      const payload = { ...editData };
      if (payload.foodAllergiesStr !== undefined) {
        payload.foodAllergies = payload.foodAllergiesStr
          .split(',')
          .map(item => item.trim())
          .filter(item => item !== ""); // กรองไอ้พวกที่เว้นว่างไว้ทิ้ง
      }

      const res = await axios.put('http://localhost:5000/api/profile/update', payload, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(res.data.user);
      
      // 🟢 อัปเดตหน้าจอให้ตรงกับที่เซฟ
      setEditData({
        ...res.data.user,
        foodAllergiesStr: res.data.user.foodAllergies ? res.data.user.foodAllergies.join(', ') : ''
      });

      Swal.fire({ toast: true, position: 'top-end', showConfirmButton: false, timer: 2000, icon: 'success', title: 'บันทึกเรียบร้อย' });
    } catch (err) {
      Swal.fire({ icon: 'error', title: 'Error' });
    } finally {
      setIsLoading(false);
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    if (passwordData.newPassword !== passwordData.confirmPassword) return Swal.fire({ icon: 'warning', text: 'รหัสไม่ตรงกัน' });
    setIsPasswordLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put('http://localhost:5000/api/auth/change-password', passwordData, { headers: { Authorization: `Bearer ${token}` } });
      Swal.fire({ toast: true, position: 'top-end', icon: 'success', title: 'อัปเดตรหัสผ่านแล้ว', timer: 2000 });
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
    } catch (err) {
      Swal.fire({ icon: 'error', text: err.response?.data?.message });
    } finally {
      setIsPasswordLoading(false);
    }
  };

  const handleForgotPassword = async () => {
    setIsPasswordLoading(true);
    try {
      await axios.post('http://localhost:5000/api/auth/forgot-password', { email: user.email });
      Swal.fire({ toast: true, position: 'top-end', icon: 'success', title: 'ส่งรหัสไปที่เมลแล้ว', showConfirmButton: false, timer: 3000 });
      setPasswordStep('reset'); 
    } catch (error) {
      Swal.fire({ icon: 'error', title: 'Error', text: error.response?.data?.message || 'ส่งเมลไม่สำเร็จ' });
    } finally {
      setIsPasswordLoading(false);
    }
  };

  const handleResetSubmit = async (e) => {
    e.preventDefault();
    if (passwordData.newPassword !== passwordData.confirmPassword) return Swal.fire({ icon: 'warning', text: 'รหัสใหม่ไม่ตรงกัน' });
    setIsPasswordLoading(true);
    try {
      await axios.post('http://localhost:5000/api/auth/reset-password', { 
        email: user.email, 
        code: resetCode, 
        newPassword: passwordData.newPassword 
      });
      Swal.fire({ toast: true, position: 'top-end', icon: 'success', title: 'เปลี่ยนรหัสผ่านใหม่เรียบร้อย!', showConfirmButton: false, timer: 3000 });
      setPasswordStep('normal'); 
      setResetCode('');
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
    } catch (error) {
      Swal.fire({ icon: 'error', text: error.response?.data?.message || 'รหัสผิดหรือหมดอายุ' });
    } finally {
      setIsPasswordLoading(false);
    }
  };

  if (!user) return <div className="min-h-screen bg-gray-50 dark:bg-[#0a0a0a] flex items-center justify-center"><div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full"></div></div>;

  return (
    <div className="min-h-screen bg-[#fafbfa] dark:bg-[#0a0a0a] text-gray-800 dark:text-gray-100 font-sans flex transition-colors duration-300">
      <SettingsSidebar />
      <SettingsNavbar user={user} />

      <input type="file" ref={fileInputRef} onChange={handleAvatarUpload} className="hidden" accept="image/*" />

      <main className="ml-[260px] mt-[70px] flex-1 p-8">
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white mb-6">Account settings</h1>

        <div className="bg-white dark:bg-[#131314] rounded-xl shadow-[0_2px_10px_rgba(0,0,0,0.04)] border border-gray-100 dark:border-white/10 flex min-h-[600px] overflow-hidden transition-colors">
          
          <div className="w-[240px] border-r border-gray-100 dark:border-white/10 p-6 flex flex-col gap-2">
            <button onClick={() => {setActiveTab('profile'); setPasswordStep('normal');}} className={`flex items-center gap-3 w-full px-4 py-3 text-sm rounded-lg text-left transition-colors ${activeTab === 'profile' ? 'text-blue-700 bg-blue-50 dark:text-blue-400 dark:bg-blue-600/10 font-semibold' : 'text-gray-500 dark:text-gray-400 font-medium hover:text-gray-800 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-white/5'}`}>
              <FaRegUserCircle className="text-lg" /> Profile Settings
            </button>
            <button onClick={() => setActiveTab('password')} className={`flex items-center gap-3 w-full px-4 py-3 text-sm rounded-lg text-left transition-colors ${activeTab === 'password' ? 'text-blue-700 bg-blue-50 dark:text-blue-400 dark:bg-blue-600/10 font-semibold' : 'text-gray-500 dark:text-gray-400 font-medium hover:text-gray-800 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-white/5'}`}>
              <FaLock className="text-lg" /> Password
            </button>
          </div>

          <div className="flex-1 p-8 md:p-12 overflow-y-auto">
            {activeTab === 'profile' && (
              <div className="animate-in fade-in duration-300">
                <div className="flex items-center gap-6 mb-10">
                  <div className="relative">
                    <div className={`w-28 h-28 rounded-full overflow-hidden border border-gray-100 dark:border-white/10 flex items-center justify-center transition-all ${isAvatarLoading ? 'opacity-50' : 'bg-[#f0f2f5] dark:bg-white/5'}`}>
                      {user.avatar ? (
                        <img src={user.avatar} alt="avatar" className="w-full h-full object-cover" />
                      ) : (
                        <div className="text-[#adb5bd] dark:text-gray-500 text-5xl"><FaUser /></div>
                      )}
                      {isAvatarLoading && (
                        <div className="absolute inset-0 flex items-center justify-center bg-white/40 dark:bg-black/40 backdrop-blur-sm">
                           <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                        </div>
                      )}
                    </div>
                    <button onClick={() => fileInputRef.current.click()} className="absolute bottom-1 right-1 bg-blue-600 text-white p-2.5 rounded-full border-4 border-white dark:border-[#131314] hover:bg-blue-700 shadow-md transition-all active:scale-90">
                      <FaCamera className="text-xs" />
                    </button>
                  </div>
                  <div className="flex gap-3">
                    <button onClick={() => fileInputRef.current.click()} disabled={isAvatarLoading} className="px-5 py-2.5 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-sm disabled:opacity-50">Upload New</button>
                    <button onClick={handleDeleteAvatar} disabled={isAvatarLoading || !user.avatar} className="px-5 py-2.5 bg-gray-100 dark:bg-white/10 text-gray-700 dark:text-gray-300 text-sm font-semibold rounded-lg hover:bg-red-50 dark:hover:bg-red-500/20 hover:text-red-600 dark:hover:text-red-400 transition-colors disabled:opacity-50">Delete avatar</button>
                  </div>
                </div>

                <form onSubmit={handleSave} className="space-y-6 max-w-3xl">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Name <span className="text-red-500">*</span></label>
                      <input type="text" name="name" value={editData.name || ''} onChange={handleChange} className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-white/10 bg-white dark:bg-white/5 text-gray-800 dark:text-white outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 transition-all text-sm" />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Email <span className="text-red-500">*</span></label>
                      <input type="email" value={user.email || ''} disabled className="w-full px-4 py-3 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/10 text-gray-500 dark:text-gray-400 outline-none text-sm cursor-not-allowed" />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Gender</label>
                      <div className="flex gap-4">
                        <label className="flex-1 flex items-center justify-center gap-2 px-4 py-3 border border-gray-300 dark:border-white/10 rounded-lg cursor-pointer hover:border-blue-500 transition-colors has-[:checked]:border-blue-600 dark:has-[:checked]:border-blue-500 has-[:checked]:bg-blue-50 dark:has-[:checked]:bg-blue-500/10">
                          <input type="radio" name="gender" value="male" checked={editData.gender === 'male'} onChange={handleChange} className="w-4 h-4 text-blue-600" />
                          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Male</span>
                        </label>
                        <label className="flex-1 flex items-center justify-center gap-2 px-4 py-3 border border-gray-300 dark:border-white/10 rounded-lg cursor-pointer hover:border-blue-500 transition-colors has-[:checked]:border-blue-600 dark:has-[:checked]:border-blue-500 has-[:checked]:bg-blue-50 dark:has-[:checked]:bg-blue-500/10">
                          <input type="radio" name="gender" value="female" checked={editData.gender === 'female'} onChange={handleChange} className="w-4 h-4 text-blue-600" />
                          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Female</span>
                        </label>
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 flex justify-between">
                        Birth Date
                        <span className="text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-600/20 px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider">Age: {calculateAge(editData.birthDate)} years</span>
                      </label>
                      <input type="date" name="birthDate" value={editData.birthDate ? editData.birthDate.split('T')[0] : ''} onChange={handleChange} className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-white/10 bg-white dark:bg-white/5 text-gray-800 dark:text-white outline-none focus:border-blue-600 text-sm" />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Weight (kg)</label>
                      <input type="number" name="weight" value={editData.weight || ''} onChange={handleChange} className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-white/10 bg-white dark:bg-white/5 text-gray-800 dark:text-white text-sm" />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Height (cm)</label>
                      <input type="number" name="height" value={editData.height || ''} onChange={handleChange} className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-white/10 bg-white dark:bg-white/5 text-gray-800 dark:text-white text-sm" />
                    </div>
                  </div>

             
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 border-t border-gray-100 dark:border-white/5 pt-6 mt-6">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Dietary Preference</label>
                      <select 
                        name="dietaryPreference" 
                        value={editData.dietaryPreference || 'none'} 
                        onChange={handleChange} 
                        className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-white/10 bg-white dark:bg-white/5 text-gray-800 dark:text-white outline-none focus:border-blue-600 text-sm appearance-none"
                      >
                        <option value="none">ทั่วไป (None)</option>
                        <option value="vegetarian">มังสวิรัติ (Vegetarian)</option>
                        <option value="vegan">วีแกน (Vegan)</option>
                        <option value="halal">ฮาลาล (Halal)</option>
                        <option value="keto">คีโต (Keto)</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Food Allergies</label>
                      <input 
                        type="text" 
                        name="foodAllergiesStr" 
                        value={editData.foodAllergiesStr || ''} 
                        onChange={handleChange} 
                        placeholder="เช่น ถั่ว, นม, อาหารทะเล (คั่นด้วยลูกน้ำ)"
                        className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-white/10 bg-white dark:bg-white/5 text-gray-800 dark:text-white outline-none focus:border-blue-600 text-sm" 
                      />
                    </div>
                  </div>

                  <div className="pt-4">
                    <button type="submit" disabled={isLoading || isAvatarLoading} className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 shadow-lg shadow-blue-600/30 active:scale-95 flex items-center gap-2">
                      {isLoading && <span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span>}
                      Save Changes
                    </button>
                  </div>
                </form>
              </div>
            )}

            {activeTab === 'password' && (
              <div className="animate-in fade-in slide-in-from-bottom-2 duration-300 max-w-xl">
                 <div className="mb-8">
                  <h2 className="text-xl font-bold text-gray-800 dark:text-white mb-1">
                    {passwordStep === 'normal' ? 'Change Password' : 'Reset Password'}
                  </h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {passwordStep === 'normal' ? 'Update your password to keep your account secure.' : `ส่งรหัสลับไปที่ ${user.email} แล้ว`}
                  </p>
                </div>

                {passwordStep === 'normal' ? (
                  <form onSubmit={handlePasswordSubmit} className="space-y-6">
                    <div className="space-y-2">
                      <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Current Password</label>
                      <input type="password" name="currentPassword" required value={passwordData.currentPassword} onChange={(e) => setPasswordData({...passwordData, currentPassword: e.target.value})} className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-white/10 bg-white dark:bg-white/5 text-gray-800 dark:text-white outline-none focus:border-blue-600 text-sm" />
                      
                      <div className="flex justify-end px-1">
                        <button 
                          type="button" 
                          onClick={handleForgotPassword} 
                          disabled={isPasswordLoading}
                          className="text-[11px] font-medium text-gray-500 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors uppercase tracking-wider disabled:opacity-50"
                        >
                          {isPasswordLoading ? 'Sending...' : 'Forgot password?'}
                        </button>
                      </div>
                    </div>

                    <div className="border-t border-gray-100 dark:border-white/5 my-6 pt-6 space-y-6">
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">New Password</label>
                        <input type="password" name="newPassword" required minLength="6" value={passwordData.newPassword} onChange={(e) => setPasswordData({...passwordData, newPassword: e.target.value})} className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-white/10 bg-white dark:bg-white/5 text-gray-800 dark:text-white outline-none focus:border-blue-600 text-sm" />
                      </div>
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Confirm New Password</label>
                        <input type="password" name="confirmPassword" required minLength="6" value={passwordData.confirmPassword} onChange={(e) => setPasswordData({...passwordData, confirmPassword: e.target.value})} className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-white/10 bg-white dark:bg-white/5 text-gray-800 dark:text-white outline-none focus:border-blue-600 text-sm" />
                      </div>
                    </div>
                    <button type="submit" disabled={isPasswordLoading} className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 shadow-lg shadow-blue-600/30 active:scale-95 flex items-center gap-2">
                      {isPasswordLoading && <span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span>}
                      Update Password
                    </button>
                  </form>
                ) : (
                  <form onSubmit={handleResetSubmit} className="space-y-6 animate-in slide-in-from-right-8 duration-300">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Verification Code</label>
                      <input 
                        type="text" required maxLength="6" placeholder="6 หลักจากเมล"
                        value={resetCode} onChange={(e) => setResetCode(e.target.value)} 
                        className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-white/10 bg-white dark:bg-white/5 text-gray-800 dark:text-white outline-none focus:border-blue-600 text-center tracking-[0.5em] font-bold text-xl" 
                      />
                    </div>
                    
                    <div className="border-t border-gray-100 dark:border-white/5 my-6 pt-6 space-y-6">
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">New Password</label>
                        <input type="password" name="newPassword" required minLength="6" value={passwordData.newPassword} onChange={(e) => setPasswordData({...passwordData, newPassword: e.target.value})} className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-white/10 bg-white dark:bg-white/5 text-gray-800 dark:text-white outline-none focus:border-blue-600 text-sm" />
                      </div>
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Confirm New Password</label>
                        <input type="password" name="confirmPassword" required minLength="6" value={passwordData.confirmPassword} onChange={(e) => setPasswordData({...passwordData, confirmPassword: e.target.value})} className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-white/10 bg-white dark:bg-white/5 text-gray-800 dark:text-white outline-none focus:border-blue-600 text-sm" />
                      </div>
                    </div>
                    
                    <div className="flex gap-4">
                      <button type="submit" disabled={isPasswordLoading} className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 shadow-lg shadow-blue-600/30 active:scale-95 flex items-center gap-2 transition-all">
                        {isPasswordLoading && <span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span>}
                        Confirm & Reset
                      </button>
                      <button type="button" onClick={() => setPasswordStep('normal')} className="px-6 py-3 bg-gray-100 dark:bg-white/10 text-gray-700 dark:text-gray-300 font-semibold rounded-lg hover:bg-gray-200 dark:hover:bg-white/20 transition-colors">
                        Cancel
                      </button>
                    </div>
                  </form>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default UserProfile;