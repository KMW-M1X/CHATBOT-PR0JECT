import { Link } from 'react-router-dom';

function Sidebar({ isExpanded, toggleSidebar }) {
  return (
    <aside 
      // 🟢 แก้ 1: พื้นหลังและเส้นขอบ (เพิ่ม bg-gray-50 สำหรับสว่าง)
      className={`flex flex-col h-screen bg-gray-50 dark:bg-[#131314] text-gray-800 dark:text-[#e3e3e3] transition-colors duration-300 ease-in-out z-20 shrink-0 border-r border-gray-200 dark:border-white/[0.05] relative
      ${isExpanded ? 'w-[280px]' : 'w-[72px]'}`}
    >
      
      {/* 1. ปุ่ม Hamburger */}
      <div className="flex items-center h-[72px] px-3">
        <button 
          onClick={toggleSidebar} 
          // 🟢 แก้ 2: สีตอน hover (เพิ่ม hover:bg-gray-200)
          className="p-3 rounded-full hover:bg-gray-200 dark:hover:bg-white/10 active:bg-gray-300 dark:active:bg-white/5 transition-all flex items-center justify-center ml-1"
        >
          <span className="material-symbols-outlined text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 transition-colors" style={{ fontVariationSettings: "'wght' 300" }}>menu</span>
        </button>
      </div>

      {/* 2. ปุ่ม แชทใหม่ (New Chat) */}
      <div className="px-4 mt-2">
        <Link 
          to="/" 
          // 🟢 แก้ 3: พื้นหลังปุ่มแชทใหม่ (เพิ่ม bg-white สำหรับสว่าง)
          className={`flex items-center gap-3 h-[44px] rounded-full bg-white dark:bg-[#1e1f20] hover:bg-gray-100 dark:hover:bg-[#2a2b2e] transition-all duration-300 border border-gray-200 dark:border-white/5 shadow-sm overflow-hidden
            ${isExpanded ? 'w-full px-4' : 'w-[44px] justify-center ml-0'}`}
        >
          <span className="material-symbols-outlined text-gray-600 dark:text-gray-300 shrink-0" style={{ fontVariationSettings: "'wght' 300" }}>add</span>
          <span className={`whitespace-nowrap text-[14px] font-medium text-gray-800 dark:text-gray-200 transition-opacity duration-300
            ${isExpanded ? 'opacity-100' : 'opacity-0 hidden'}`}>
            แชทใหม่
          </span>
        </Link>
      </div>

      {/* 3. หมวด ประวัติการแชท (Recent) */}
      <div className="flex-1 overflow-y-auto mt-8 px-3 scrollbar-none">
        <div className={`text-[12px] font-semibold text-gray-500 dark:text-gray-500 uppercase tracking-wider px-4 mb-3 transition-opacity duration-300
          ${isExpanded ? 'opacity-100' : 'opacity-0 hidden'}`}>
          ล่าสุด
        </div>

        <div className="space-y-1">
          <Link 
            to="/"
            // 🟢 แก้ 4: ปุ่มประวัติแชท (เพิ่ม hover:bg-gray-200 สำหรับสว่าง)
            className={`flex items-center gap-3 p-3 rounded-2xl hover:bg-gray-200 dark:hover:bg-[#1e1f20] transition-colors cursor-pointer group
                ${isExpanded ? 'justify-start px-4' : 'justify-center mx-1'}`}
          >
            <span className="material-symbols-outlined text-gray-500 group-hover:text-gray-800 dark:group-hover:text-gray-300 shrink-0 transition-colors" style={{ fontVariationSettings: "'wght' 300", fontSize: '18px' }}>chat_bubble</span>
            <span className={`whitespace-nowrap text-[14px] text-gray-600 dark:text-gray-400 group-hover:text-gray-900 dark:group-hover:text-gray-200 truncate transition-all duration-300
              ${isExpanded ? 'opacity-100' : 'opacity-0 w-full'}`}>
              AI Modelling: Rule-based...
            </span>
          </Link>
        </div>
      </div>

      {/* 4. เมนูด้านล่างสุด (Settings, Help) */}
      <div className="p-3 space-y-1 mb-3">
        {/* ปุ่มช่วยเหลือ (Help) */}
        <Link to="#" className={`flex items-center gap-3 p-3 rounded-2xl hover:bg-gray-200 dark:hover:bg-[#1e1f20] transition-colors group
          ${isExpanded ? 'justify-start px-4' : 'justify-center mx-1'}`}>
          <span className="material-symbols-outlined text-gray-500 group-hover:text-gray-800 dark:group-hover:text-gray-300 shrink-0 transition-colors" style={{ fontVariationSettings: "'wght' 300", fontSize: '20px' }}>help</span>
          <span className={`whitespace-nowrap text-[14px] text-gray-600 dark:text-gray-400 group-hover:text-gray-900 dark:group-hover:text-gray-200 transition-all duration-300
            ${isExpanded ? 'opacity-100' : 'opacity-0 hidden'}`}>
            ช่วยเหลือ
          </span>
        </Link>

        {/* ปุ่มตั้งค่า (Settings) */}
        <Link 
          to="/settings" 
          className={`flex items-center gap-3 p-3 rounded-2xl hover:bg-gray-200 dark:hover:bg-[#1e1f20] transition-colors group
          ${isExpanded ? 'justify-start px-4' : 'justify-center mx-1'}`}
        >
          <span className="material-symbols-outlined text-gray-500 group-hover:text-gray-800 dark:group-hover:text-gray-300 shrink-0 transition-colors" style={{ fontVariationSettings: "'wght' 300", fontSize: '20px' }}>settings</span>
          <span className={`whitespace-nowrap text-[14px] text-gray-600 dark:text-gray-400 group-hover:text-gray-900 dark:group-hover:text-gray-200 transition-all duration-300
            ${isExpanded ? 'opacity-100' : 'opacity-0 hidden'}`}>
            ตั้งค่า
          </span>
        </Link>
      </div>

    </aside>
  );
}

export default Sidebar;