import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import {
  DiscoverySessionList,
  UploadStep,
  MapRolesStep,
  ActivitiesStep,
  AnalysisStep,
  RoadmapStep,
} from './pages/discovery'
import { LoginPage } from './pages/auth'
import { DiscoveryErrorBoundary } from './components/features/discovery'
import { ProtectedRoute } from './components/auth'
import { AuthProvider } from './stores'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <DiscoveryErrorBoundary>
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<LoginPage />} />

            {/* Default redirect */}
            <Route path="/" element={<Navigate to="/discovery" replace />} />

            {/* Protected Discovery Routes */}
            <Route
              path="/discovery"
              element={
                <ProtectedRoute>
                  <DiscoverySessionList />
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

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/discovery" replace />} />
          </Routes>
        </DiscoveryErrorBoundary>
      </AuthProvider>
    </BrowserRouter>
  )
}
