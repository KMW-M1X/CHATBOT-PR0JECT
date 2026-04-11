import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import axios from 'axios'

import AuthLayout from './Layout/AuthLayout'
import MainLayout from './Layout/MainLayout'

// นำเข้า Pages
import Home from './Pages/Home'
import AuthModal from './Pages/AuthModal'
import ProfileSetup from './Pages/ProfileSetup'
import UserProfile from './Pages/UserProfile'

function App() {
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [user, setUser] = useState(null);
  const [isProfileSetupOpen, setIsProfileSetupOpen] = useState(false);
  const [isInitialLoading, setIsInitialLoading] = useState(true);

  // 🟢 1. สร้าง State คุม Theme ระดับ Global (ดึงค่าจากเครื่อง ถ้าไม่มีเริ่มที่ dark)
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'dark');

  // 🟢 2. useEffect สำหรับคุม Class 'dark' ที่แท็ก <html>
  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    // จำไว้ในเครื่องด้วย รีเฟรชหน้าจะได้ไม่หลุด
    localStorage.setItem('theme', theme);
  }, [theme]);

  // 🟢 3. ฟังก์ชันสลับโหมด (ส่งไปให้ Navbar ใช้)
  const toggleTheme = () => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
  };

  const fetchUserData = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      setIsInitialLoading(false);
      return;
    }

    try {
      const res = await axios.get('http://localhost:5000/api/profile/me', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(res.data);
      if (!res.data.weight || res.data.weight === 0) {
        setIsProfileSetupOpen(true);
      }
    } catch (err) {
      console.error("Token เน่าหรือหมดอายุว่ะจารย์");
      localStorage.removeItem('token');
    } finally {
      setIsInitialLoading(false);
    }
  };

  useEffect(() => {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200';
    document.head.appendChild(link);
    fetchUserData();
    return () => {
      if (document.head.contains(link)) {
        document.head.removeChild(link);
      }
    };
  }, []);

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    setIsAuthOpen(false); 
    const isProfileIncomplete = !userData.weight || userData.weight === 0 || userData.weight === "";
    if (isProfileIncomplete) {
      setIsProfileSetupOpen(true); 
    } else {
      setIsProfileSetupOpen(false);
    }
  };

  if (isInitialLoading) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center text-white">
        <div className="flex flex-col items-center gap-4">
          <span className="material-symbols-outlined animate-spin text-4xl text-emerald-500">progress_activity</span>
          <p className="font-medium tracking-widest text-gray-400">กำลังพาจารย์เข้าสู่ระบบ...</p>
        </div>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <AuthModal 
        isOpen={isAuthOpen} 
        onClose={() => setIsAuthOpen(false)} 
        onLoginSuccess={handleLoginSuccess}
      />

      <ProfileSetup 
        isOpen={isProfileSetupOpen}
        onClose={() => setIsProfileSetupOpen(false)}
        onComplete={(updatedUser) => {
          setUser(updatedUser);
          setIsProfileSetupOpen(false);
        }}
      />

      <Routes>
        {/* 🟢 4. ส่ง theme และ toggleTheme เข้าไปใน MainLayout */}
        <Route element={
          <MainLayout 
            onOpenAuth={() => setIsAuthOpen(true)} 
            user={user} 
            theme={theme} 
            toggleTheme={toggleTheme} 
          />
        }>
          <Route path="/" element={<Home />} />
        </Route>

        <Route 
          path="/settings" 
          element={
            user ? (
              <UserProfile user={user} onUpdateUser={setUser} />
            ) : (
              <Navigate to="/" replace />
            )
          } 
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App