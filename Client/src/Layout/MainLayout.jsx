import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from '../Components/Sidebar'
import Navbar from '../Components/Navbar' 

// 🟢 1. รับ theme และ toggleTheme พ่วงเข้ามาด้วย!
function MainLayout({ onOpenAuth, user, theme, toggleTheme }) {
  const [isExpanded, setIsExpanded] = useState(true)

  const toggleSidebar = () => {
    setIsExpanded(!isExpanded)
  }

  return (
    // 🟢 2. ปลดล็อคสีดำตายตัว เปลี่ยนให้รองรับทั้ง Light (bg-white) และ Dark (dark:bg-[#131314])
    <div className="flex h-screen bg-white dark:bg-[#131314] text-gray-800 dark:text-[#e3e3e3] overflow-hidden transition-colors duration-300">
      
      {/* Sidebar ยืดหดได้ */}
      <Sidebar isExpanded={isExpanded} toggleSidebar={toggleSidebar} />

      <main className="flex-1 flex flex-col h-full min-w-0 transition-all duration-300 ease-in-out">
        
        {/* 🟢 3. โยนสายไฟ (theme, toggleTheme) ต่อให้ Navbar ตรงนี้! */}
        <Navbar 
          onOpenAuth={onOpenAuth} 
          user={user} 
          theme={theme} 
          toggleTheme={toggleTheme} 
        />

        {/* พื้นที่ห้องแชท */}
        <div className="flex-1 overflow-y-auto">
          <Outlet />
        </div>
      </main>

    </div>
  )
}

export default MainLayout