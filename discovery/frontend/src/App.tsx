import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './stores/auth'
import { LoginPage } from './pages/login/LoginPage'
import {
  SessionsDashboard,
  UploadStep,
  MapRolesStep,
  ActivitiesStep,
  AnalysisStep,
  RoadmapStep,
} from './pages/discovery'

// Protected route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen bg-base flex items-center justify-center">
        <div className="text-center">
          <div className="w-10 h-10 rounded-full border-2 border-accent border-t-transparent animate-spin mx-auto mb-3" />
          <p className="text-sm text-muted">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

// App routes
function AppRoutes() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />

      {/* Protected routes */}
      <Route
        path="/discovery"
        element={
          <ProtectedRoute>
            <SessionsDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/discovery/:sessionId/upload"
        element={
          <ProtectedRoute>
            <UploadStep />
          </ProtectedRoute>
        }
      />
      <Route
        path="/discovery/:sessionId/map-roles"
        element={
          <ProtectedRoute>
            <MapRolesStep />
          </ProtectedRoute>
        }
      />
      <Route
        path="/discovery/:sessionId/activities"
        element={
          <ProtectedRoute>
            <ActivitiesStep />
          </ProtectedRoute>
        }
      />
      <Route
        path="/discovery/:sessionId/analysis"
        element={
          <ProtectedRoute>
            <AnalysisStep />
          </ProtectedRoute>
        }
      />
      <Route
        path="/discovery/:sessionId/roadmap"
        element={
          <ProtectedRoute>
            <RoadmapStep />
          </ProtectedRoute>
        }
      />

      {/* Default redirect */}
      <Route path="/" element={<Navigate to="/discovery" replace />} />
      <Route path="*" element={<Navigate to="/discovery" replace />} />
    </Routes>
  )
}

// Main app
export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
