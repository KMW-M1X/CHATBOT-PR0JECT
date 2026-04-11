import React from 'react';
import { FaSearch, FaBell, FaUser } from 'react-icons/fa';

const SettingsNavbar = ({ user }) => {
  return (
    <header className="h-[70px] bg-white dark:bg-[#131314] border-b border-gray-200 dark:border-white/10 flex justify-between items-center px-8 ml-[260px] fixed top-0 w-[calc(100%-260px)] z-10 transition-colors duration-300">
      
      {/* Breadcrumb & Search */}
      <div className="flex items-center gap-8 w-full max-w-2xl">
        <span className="text-gray-500 dark:text-gray-400 text-sm font-medium whitespace-nowrap">
          Pages / <span className="text-gray-800 dark:text-white">Settings</span>
        </span>
        
        <div className="relative w-full max-w-md hidden md:block">
          <FaSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
          <input 
            type="text" 
            placeholder="search for features..." 
            className="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-full text-sm outline-none focus:border-blue-500 dark:text-white transition-all placeholder:text-gray-400 dark:placeholder:text-gray-600"
          />
        </div>
      </div>

      {/* Right Side (Noti & Profile) */}
      <div className="flex items-center gap-6">
        <button className="text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-white transition-colors relative">
          <FaBell className="text-xl" />
          <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-white dark:border-[#131314]"></span>
        </button>
        
        <div className="flex items-center gap-3 cursor-pointer group">
          {/* ส่วนแสดงรูปโปรไฟล์ */}
          <div className="w-9 h-9 rounded-full overflow-hidden border border-gray-100 dark:border-white/10 flex items-center justify-center bg-[#f0f2f5] dark:bg-white/10">
            {user?.avatar ? (
              <img src={user.avatar} alt="profile" className="w-full h-full object-cover" />
            ) : (
              <FaUser className="text-[#adb5bd] dark:text-gray-400 text-sm" />
            )}
          </div>
          <span className="text-sm font-bold text-gray-800 dark:text-white hidden md:block group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
            {user?.name || 'User'}
          </span>
        </div>
      </div>
    </header>
  );
};

export default SettingsNavbar;