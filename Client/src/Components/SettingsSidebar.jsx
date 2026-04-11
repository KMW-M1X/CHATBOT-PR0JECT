import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  FaRegUserCircle, 
  FaSignOutAlt, 
  FaGripHorizontal, 
  FaArrowLeft 
} from 'react-icons/fa';

const SettingsSidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    localStorage.removeItem('token');
    window.location.href = '/';
  };

  return (
    // 🟢 1. พื้นหลังและเส้นขอบ ต้องสลับตามโหมด
    <aside className="w-[260px] bg-white dark:bg-[#131314] border-r border-gray-100 dark:border-white/10 h-screen fixed left-0 top-0 flex flex-col z-20 shadow-[4px_0_24px_rgba(0,0,0,0.01)] transition-colors duration-300">
      
      {/* 🟢 2. ปุ่ม Back - เปลี่ยนสี hover ให้สว่างขึ้นในโหมดมืด */}
      <div className="h-[80px] flex items-center px-8">
        <button 
          onClick={() => navigate('/')} 
          className="group flex items-center gap-3 text-gray-400 dark:text-gray-500 hover:text-gray-900 dark:hover:text-white transition-colors duration-300"
        >
          <FaArrowLeft className="text-sm transition-transform duration-300 group-hover:-translate-x-1.5" /> 
          <span className="text-sm font-semibold tracking-wide uppercase italic">Back</span>
        </button>
      </div>

      {/* Menu Items */}
      <nav className="flex-1 py-2 space-y-1">

        {/* 🟢 3. Settings (Active) - ปรับสีพื้นหลังตอน Active ให้ซอฟต์ลงในโหมดมืด */}
        <div className="px-8 py-3.5 flex items-center gap-4 text-blue-600 dark:text-blue-400 bg-blue-50/50 dark:bg-blue-600/10 border-r-4 border-blue-600 dark:border-blue-400 cursor-default">
          <FaRegUserCircle className="text-lg" /> 
          <span className="font-bold text-sm">Settings</span>
        </div>

      </nav>

      {/* 🟢 4. Logout - ปรับเส้นขอบด้านบนและสี Hover */}
      <div className="p-8 border-t border-gray-50 dark:border-white/5">
        <div 
          onClick={handleLogout}
          className="flex items-center gap-4 text-gray-400 dark:text-gray-500 hover:text-red-500 transition-colors group"
        >
          <FaSignOutAlt className="text-lg group-hover:translate-x-1 transition-transform" /> 
          <span className="font-medium text-sm">Log out</span>
        </div>
      </div>

    </aside>
  );
};

export default SettingsSidebar;