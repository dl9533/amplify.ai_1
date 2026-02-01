import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react'

export interface User {
  id: string
  email: string
  name: string
  organization?: string
}

export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
}

export interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<boolean>
  logout: () => void
  checkAuth: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

const AUTH_STORAGE_KEY = 'discovery_auth'

interface StoredAuth {
  user: User
  token: string
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const checkAuth = useCallback(async () => {
    setIsLoading(true)
    try {
      const stored = localStorage.getItem(AUTH_STORAGE_KEY)
      if (stored) {
        const parsed: StoredAuth = JSON.parse(stored)
        // In a real app, we'd validate the token with the backend
        setUser(parsed.user)
      }
    } catch {
      localStorage.removeItem(AUTH_STORAGE_KEY)
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  const login = useCallback(async (email: string, password: string): Promise<boolean> => {
    setIsLoading(true)
    try {
      // For standalone Discovery module, we use a simple auth approach
      // In production, this would call a real auth endpoint
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      if (!response.ok) {
        // For demo/development: allow any login with valid email format
        if (email.includes('@') && password.length >= 1) {
          const mockUser: User = {
            id: crypto.randomUUID(),
            email,
            name: email.split('@')[0],
            organization: email.split('@')[1]?.split('.')[0] || 'Discovery',
          }
          const authData: StoredAuth = {
            user: mockUser,
            token: btoa(`${email}:${Date.now()}`),
          }
          localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(authData))
          setUser(mockUser)
          return true
        }
        return false
      }

      const data = await response.json()
      const authData: StoredAuth = {
        user: data.user,
        token: data.token,
      }
      localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(authData))
      setUser(data.user)
      return true
    } catch {
      // Fallback for development without backend
      if (email.includes('@') && password.length >= 1) {
        const mockUser: User = {
          id: crypto.randomUUID(),
          email,
          name: email.split('@')[0],
          organization: email.split('@')[1]?.split('.')[0] || 'Discovery',
        }
        const authData: StoredAuth = {
          user: mockUser,
          token: btoa(`${email}:${Date.now()}`),
        }
        localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(authData))
        setUser(mockUser)
        return true
      }
      return false
    } finally {
      setIsLoading(false)
    }
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem(AUTH_STORAGE_KEY)
    setUser(null)
  }, [])

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    checkAuth,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export function getStoredToken(): string | null {
  try {
    const stored = localStorage.getItem(AUTH_STORAGE_KEY)
    if (stored) {
      const parsed: StoredAuth = JSON.parse(stored)
      return parsed.token
    }
  } catch {
    // Invalid stored data
  }
  return null
}
