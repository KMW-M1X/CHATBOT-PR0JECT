import { Outlet } from 'react-router-dom'

function AuthLayout() {
  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      {/* <Outlet /> คือรูโบ๋ๆ ที่เดี๋ยวหน้า Login/Register จะมาเสียบตรงนี้ */}
      <div className="w-full max-w-md">
        <Outlet /> 
      </div>
    </div>
  )
}

export default AuthLayout