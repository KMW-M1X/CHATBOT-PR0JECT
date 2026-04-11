import React from 'react';
import { Plus, Mic, Send } from 'lucide-react';

function ChatBar({ inputText, setInputText, handleSend, isChatActive }) {
  // กด Enter เพื่อส่ง (กด Shift+Enter ถึงจะขึ้นบรรทัดใหม่)
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div 
      className={`absolute left-0 w-full px-4 transition-all duration-700 ease-[cubic-bezier(0.2,0.8,0.2,1)] flex flex-col items-center z-10 ${
        isChatActive 
          // 🟢 รองรับ Dark/Light Mode ตอนแชทเด้งลงข้างล่าง
          ? 'bottom-0 pb-6 bg-gradient-to-t from-white via-white to-transparent dark:from-[#131314] dark:via-[#131314] dark:to-transparent pt-10' 
          : 'top-[45%] -translate-y-1/2' // ลอยอยู่ตรงกลาง
      }`}
    >
      {/* 🟢 ข้อความทักทาย Welcome to SillyBot */}
      {!isChatActive && (
        <h1 className="text-4xl sm:text-5xl font-bold mb-8 bg-gradient-to-r from-blue-500 via-purple-500 to-orange-400 text-transparent bg-clip-text animate-in fade-in zoom-in-95 duration-700 text-center tracking-tight">
          Welcome to SillyBot
        </h1>
      )}

      <div className="max-w-3xl w-full">
        {/* 🟢 กล่องพิมพ์ (รองรับ Dark Mode) */}
        <div className="relative bg-gray-50 dark:bg-[#1e1f20] rounded-[32px] p-2 flex flex-col border border-gray-200 dark:border-white/10 shadow-lg focus-within:shadow-xl dark:focus-within:bg-[#252628] transition-all duration-300">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="พิมพ์มาเลย"
            className="w-full bg-transparent text-gray-900 dark:text-[#e3e3e3] placeholder-gray-500 dark:placeholder-gray-400 px-4 py-3.5 min-h-[56px] max-h-[200px] outline-none resize-none text-[16px]"
            rows="1"
          />
          
          <div className="flex items-center justify-between px-2 pb-1">
            <div className="flex items-center gap-1">
              <button className="p-2 hover:bg-gray-200 dark:hover:bg-white/10 rounded-full transition-colors text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200">
                <Plus size={20} />
              </button>
            </div>
            
            <div className="flex items-center gap-2">
              {/* 🟢 สลับปุ่ม ไมค์/ส่งข้อความ อัตโนมัติ */}
              {inputText.trim() ? (
                <button 
                  onClick={handleSend} 
                  className="p-2 bg-blue-600 hover:bg-blue-700 dark:bg-white/10 dark:hover:bg-white/20 rounded-full transition-colors text-white animate-in zoom-in duration-200 shadow-md"
                >
                  <Send size={18} />
                </button>
              ) : (
                <button className="p-2 hover:bg-gray-200 dark:hover:bg-white/10 rounded-full transition-colors text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200">
                  <Mic size={20} />
                </button>
              )}
            </div>
          </div>
        </div>
        
        {/* 🟢 คำเตือนใต้กล่องแชท */}
        <div className="text-center mt-3 text-[12px] text-gray-500 dark:text-gray-400 font-medium">
          ข้อมูลที่แชทบอทตอบนี้อาจ<span className="font-semibold">ไม่ถูกต้อง</span> เสมอไป
        </div>
      </div>
    </div>
  );
}

export default ChatBar;