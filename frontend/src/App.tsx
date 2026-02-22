import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import AppLayout from './components/layout/AppLayout'

import Login from './pages/Login'
import Signup from './pages/Signup'
import Home from './pages/Home'
import ChatPage from './pages/ChatPage'
import Settings from './pages/Settings'

function App() {
  // hooks
  // loading state
  const { user } = useAuth()

  // routing config
  return (
    <Routes>
      {/* ===================== */}
      {/* PUBLIC route  */}
      {/* ===================== */}
      {/* login route  */}
      <Route 
        path="/login"
        element={user ? <Navigate to="/" replace /> : <Login />}
      />

      {/* sign up route  */}
      <Route 
        path="/signup"
        element={user ? <Navigate to="/" replace /> : <Signup />}
      />

      {/* Chat page - publicly accessible for sharing */}
      <Route element={<AppLayout />}>
        <Route path="/chat/:sessionId" element={<ChatPage/>} />
      </Route>

      {/* ===================== */}
      {/* PROTECTED routes  */}
      {/* ===================== */}
      {/* Home route  */}
      <Route 
        element={
          // Wrap page in ProtectedRoute
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Home />}/>
        <Route path="/settings" element={<Settings />}/>
      </Route>

      {/* ===================== */}
      {/* CATCH-all route  */}
      {/* ===================== */}
      <Route 
        path="*"
        element={<Navigate to="/" replace />}
      />
    </Routes>
  )
}

export default App