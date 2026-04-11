import React, { useState, useCallback } from 'react';
import axios from 'axios';
import Swal from 'sweetalert2'; 
import { useDropzone } from 'react-dropzone';
import { 
  FaWeight, FaRulerVertical, FaLeaf, FaCheckCircle, 
  FaCamera, FaUser, FaVenusMars, FaCalendarAlt 
} from 'react-icons/fa';

function ProfileSetup({ isOpen, onClose, onComplete }) {
  // 1. State setup
  const [isLoading, setIsLoading] = useState(false);
  const [isUploadingImg, setIsUploadingImg] = useState(false);
  const [imageFile, setImageFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [formData, setFormData] = useState({
    weight: '',
    height: '',
    gender: '', // Add gender
    birthDate: '', // Add birth date
    dietaryPreference: 'none',
    foodAllergies: '',
    avatar: '' 
  });

  // 2. Form handler
  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  // 3. Dropzone handler
  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0];
    if (file) {
      setImageFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    accept: { 'image/*': [] }, 
    maxFiles: 1 
  });

  // 4. Cloudinary upload
  const uploadToCloudinary = async (file) => {
    const cloudName = import.meta.env.VITE_CLOUDINARY_CLOUD_NAME; 
    const uploadPreset = import.meta.env.VITE_CLOUDINARY_UPLOAD_PRESET; 

    if (!cloudName || !uploadPreset) {
      throw new Error('Cloudinary config is missing in .env file');
    }

    const cloudinaryData = new FormData();
    cloudinaryData.append('file', file);
    cloudinaryData.append('upload_preset', uploadPreset);

    const res = await axios.post(
      `https://api.cloudinary.com/v1_1/${cloudName}/image/upload`, 
      cloudinaryData
    );
    return res.data.secure_url;
  };

  // 5. Submit handler
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      let avatarUrl = formData.avatar;

      if (imageFile) {
        setIsUploadingImg(true);
        avatarUrl = await uploadToCloudinary(imageFile);
        setIsUploadingImg(false);
      }

      const token = localStorage.getItem('token');
      const dataToSubmit = { ...formData, avatar: avatarUrl };

      const response = await axios.put(
       'http://localhost:5000/api/profile/update',
        dataToSubmit,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      await Swal.fire({
        icon: 'success',
        title: 'บันทึกเรียบร้อย!',
        text: 'ข้อมูลโปรไฟล์อัปเดตแล้ว',
        background: '#131314', 
        color: '#ffffff',
        confirmButtonColor: '#10b981', 
        confirmButtonText: 'ลุยเลย'
      });

      if (onComplete) onComplete(response.data.user);
      if (onClose) onClose();

    } catch (error) {
      console.error("Error:", error);
      Swal.fire({
        icon: 'error',
        title: 'บันทึกไม่สำเร็จ',
        text: error.message || error.response?.data?.message || 'เกิดข้อผิดพลาดในการบันทึกข้อมูล',
        background: '#131314',
        color: '#ffffff',
        confirmButtonColor: '#ef4444'
      });
    } finally {
      setIsLoading(false);
      setIsUploadingImg(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black/80 backdrop-blur-lg p-4 animate-in fade-in duration-300 overflow-y-auto">
      
      <div className="relative w-full max-w-[600px] bg-[#131314]/90 rounded-3xl shadow-[0_0_80px_rgba(16,185,129,0.15)] border border-white/10 overflow-hidden animate-in zoom-in-95 ease-out duration-300 p-8 sm:p-10 my-8">
        
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-white tracking-tight mb-2">
            อัปเดตโปรไฟล์
          </h2>
          <p className="text-[#a1a1aa] text-sm">
            เพิ่มรูปและข้อมูลสุขภาพ
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          
          {/* Avatar Upload */}
          <div className="flex flex-col items-center justify-center mb-6">
            <div 
              {...getRootProps()} 
              className={`relative w-32 h-32 rounded-full border-2 border-dashed flex items-center justify-center cursor-pointer transition-all group overflow-hidden ${
                isDragActive 
                  ? 'border-emerald-400 bg-emerald-500/20 scale-105' 
                  : 'border-emerald-500/50 bg-white/5 hover:bg-white/10 hover:border-emerald-400'
              }`}
            >
              <input {...getInputProps()} />
              
              {previewUrl ? (
                <img src={previewUrl} alt="Preview" className="w-full h-full object-cover" />
              ) : (
                <FaUser className={`text-5xl transition-colors ${isDragActive ? 'text-emerald-400' : 'text-gray-500 group-hover:text-emerald-400'}`} />
              )}
              
              <div className={`absolute inset-0 bg-black/60 flex flex-col items-center justify-center transition-opacity ${isDragActive ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}>
                <FaCamera className="text-white text-2xl mb-1" />
                <span className="text-white text-xs font-medium">
                  {isDragActive ? 'วางรูปลงที่นี่' : 'ลากไฟล์หรือคลิก'}
                </span>
              </div>
            </div>
          </div>
          
          {/* Gender & Birth Date */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">เพศ (Gender)</label>
              <div className="relative">
                <FaVenusMars className="absolute top-4 left-4 text-gray-500" />
                <select 
                  name="gender" 
                  required 
                  value={formData.gender} 
                  onChange={handleChange}
                  className="w-full pl-11 pr-4 py-3 bg-[#1e1f20] text-white border border-white/10 rounded-xl focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all appearance-none cursor-pointer"
                >
                  <option value="" disabled>เลือกเพศ</option>
                  <option value="male">ชาย (Male)</option>
                  <option value="female">หญิง (Female)</option>
                  <option value="other">อื่นๆ (Other)</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">วันเกิด (Date of Birth)</label>
              <div className="relative">
                <FaCalendarAlt className="absolute top-4 left-4 text-gray-500" />
                <input 
                  type="date" 
                  name="birthDate" 
                  required 
                  value={formData.birthDate} 
                  onChange={handleChange}
                  // [color-scheme:dark] ensures the date picker icon is visible on dark backgrounds
                  className="w-full pl-11 pr-4 py-3 bg-white/5 text-white border border-white/10 rounded-xl focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all [color-scheme:dark]"
                />
              </div>
            </div>
          </div>

          {/* Weight & Height */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">น้ำหนัก (kg)</label>
              <div className="relative">
                <FaWeight className="absolute top-4 left-4 text-gray-500" />
                <input 
                  type="number" name="weight" required placeholder="เช่น 65" 
                  value={formData.weight} onChange={handleChange}
                  className="w-full pl-11 pr-4 py-3 bg-white/5 text-white border border-white/10 rounded-xl focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all placeholder:text-gray-600"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">ส่วนสูง (cm)</label>
              <div className="relative">
                <FaRulerVertical className="absolute top-4 left-4 text-gray-500" />
                <input 
                  type="number" name="height" required placeholder="เช่น 175" 
                  value={formData.height} onChange={handleChange}
                  className="w-full pl-11 pr-4 py-3 bg-white/5 text-white border border-white/10 rounded-xl focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all placeholder:text-gray-600"
                />
              </div>
            </div>
          </div>

          {/* Dietary Preference */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">รูปแบบการกิน (Dietary)</label>
            <div className="relative">
              <FaLeaf className="absolute top-4 left-4 text-gray-500" />
              <select 
                name="dietaryPreference" 
                value={formData.dietaryPreference} onChange={handleChange}
                className="w-full pl-11 pr-4 py-3 bg-[#1e1f20] text-white border border-white/10 rounded-xl focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all appearance-none cursor-pointer"
              >
                <option value="none">กินแหลก ไม่เลือก (None)</option>
                <option value="vegetarian">มังสวิรัติ (Vegetarian)</option>
                <option value="vegan">วีแกน (Vegan)</option>
                <option value="keto">คีโตเจนิค (Keto)</option>
                <option value="halal">ฮาลาล (Halal)</option>
              </select>
            </div>
          </div>

          {/* Food Allergies */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">อาหารที่แพ้ (ถ้ามี)</label>
            <textarea 
              name="foodAllergies" 
              rows="2" placeholder="เช่น ถั่วลิสง, นมวัว, อาหารทะเล (เว้นว่างได้ถ้าไม่แพ้อะไร)" 
              value={formData.foodAllergies} onChange={handleChange}
              className="w-full p-4 bg-white/5 text-white border border-white/10 rounded-xl focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all placeholder:text-gray-600 resize-none"
            />
          </div>

          <button 
            type="submit" disabled={isLoading || isUploadingImg}
            className="w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-4 px-4 rounded-xl transition-all shadow-lg shadow-emerald-500/20 active:scale-[0.98] disabled:opacity-50 mt-4"
          >
            {isLoading || isUploadingImg ? (
              <>
                <span className="material-symbols-outlined animate-spin">progress_activity</span>
                <span>{isUploadingImg ? 'กำลังอัปโหลด...' : 'กำลังบันทึก...'}</span>
              </>
            ) : (
              <>
                <FaCheckCircle /> บันทึกและเริ่มใช้งาน
              </>
            )}
          </button>

        </form>
      </div>
    </div>
  );
}

export default ProfileSetup;