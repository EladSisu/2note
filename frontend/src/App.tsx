import { Route, BrowserRouter as Router, Routes, Navigate } from 'react-router-dom'
import { ProtectedRoute } from './components/ProtectedRoute.tsx'
import { AuthProvider } from './contexts/AuthContext.tsx'
import Auth from './pages/Auth.tsx'
import Dashboard from './pages/Dashboard.tsx'
import Document from './pages/Document.tsx'
import LandingPage from './pages/LandingPage.tsx'

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/auth" element={<Auth />} />
          <Route
            path="/documents"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/documents/:id"
            element={
              <ProtectedRoute>
                <Document />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </AuthProvider>
    </Router>
  )
}

export default App
