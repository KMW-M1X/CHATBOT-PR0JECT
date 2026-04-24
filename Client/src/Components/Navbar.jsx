import React from 'react';
import { Link } from 'react-router-dom';
import { FaUser } from 'react-icons/fa'; // 🟢 ใช้ FaUser เพื่อความคลีน

function UserProfileButton({ user, onOpenAuth }) {
  if (user) {
    return (
      <Link to="/settings">
        <div 
          className="w-9 h-9 rounded-full bg-gradient-to-tr from-blue-500 via-purple-500 to-pink-500 p-[2px] cursor-pointer ml-3 hover:scale-110 transition-all shadow-lg shadow-blue-500/20 active:scale-95" 
          title="ไปที่ตั้งค่าโปรไฟล์"
        >
          {/* 🟢 เช็คว่ามีรูปมั้ย ถ้าไม่มีให้โชว์ไอคอนคนพื้นหลังเทา */}
          {user.avatar ? (
            <img 
              src={user.avatar} 
              alt="Profile" 
              className="w-full h-full rounded-full bg-white dark:bg-[#1e1f20] object-cover border border-gray-200 dark:border-[#131314]" 
            />
          ) : (
            <div className="w-full h-full rounded-full bg-[#f0f2f5] dark:bg-[#2a2b2e] flex items-center justify-center text-[#9ca3af]">
              <FaUser className="text-[14px]" />
            </div>
          )}
        </div>
      </Link>
    );
  }

  return (
    <button 
      onClick={onOpenAuth}
      className="px-5 py-2 ml-3 text-[14px] font-semibold bg-blue-100 hover:bg-blue-200 text-blue-800 dark:bg-[#8ab4f8] dark:hover:bg-[#a8c7fa] dark:text-[#131314] rounded-full transition-all duration-300 whitespace-nowrap shadow-md dark:hover:shadow-blue-500/20 active:scale-95"
    >
      เข้าสู่ระบบ
    </button>
  );
}

function Navbar({ title = "เดี๋ยวมาทำระบบTitle", onOpenAuth, user, theme, toggleTheme }) {
  return (
    <header className="flex items-center justify-between px-6 py-3 shrink-0 bg-white/90 dark:bg-[#131314]/80 backdrop-blur-md text-gray-800 dark:text-[#e3e3e3] border-b border-gray-200 dark:border-white/[0.05] z-10 sticky top-0 transition-colors duration-300">
      <Link to="/" className="text-xl font-semibold tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-gray-900 to-gray-600 dark:from-gray-100 dark:to-gray-400 hover:opacity-80 transition-opacity">
        ChatBot
      </Link>
      
      <div className="hidden md:flex flex-row items-center gap-2 cursor-pointer hover:bg-black/5 dark:hover:bg-white/5 px-4 py-2 rounded-xl transition-all duration-300 border border-transparent hover:border-gray-200 dark:hover:border-white/5">
        <span className="text-[14px] font-medium text-gray-700 dark:text-gray-300 truncate max-w-[400px]">
          {title}
        </span>
      </div>

      <div className="flex items-center gap-1 sm:gap-2">
        <button 
          onClick={toggleTheme}
          className="p-2.5 hover:bg-black/10 dark:hover:bg-white/10 rounded-full transition-all duration-300 flex items-center justify-center text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 active:scale-95"
        >
          <span className="material-symbols-outlined transition-transform duration-500" style={{ fontVariationSettings: "'wght' 300", fontSize: '20px' }}>
            {theme === 'dark' ? 'light_mode' : 'dark_mode'}
          </span>
        </button>

        <button className="p-2 hover:bg-black/10 dark:hover:bg-white/10 rounded-full transition-all duration-300 flex items-center justify-center text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 active:scale-95">
          <span className="material-symbols-outlined" style={{ fontVariationSettings: "'wght' 300", fontSize: '20px' }}>
            more_vert
          </span>
        </button>
        
        <UserProfileButton user={user} onOpenAuth={onOpenAuth} />
      </div>
    </header>
  );
}

export default Navbar;