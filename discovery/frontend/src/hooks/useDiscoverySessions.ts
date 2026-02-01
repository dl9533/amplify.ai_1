import { useState, useCallback, useEffect } from 'react'

export type SessionStatus = 'Draft' | 'In Progress' | 'Completed' | 'Archived'

export interface DiscoverySession {
  id: string
  name: string
  status: SessionStatus
  currentStep: number
  totalSteps: number
  createdAt: string
  updatedAt: string
}

export interface UseDiscoverySessionsReturn {
  sessions: DiscoverySession[]
  isLoading: boolean
  error: string | null
  page: number
  totalPages: number
  setPage: (page: number) => void
  createSession: (name: string) => Promise<DiscoverySession>
  deleteSession: (id: string) => Promise<void>
  isCreating: boolean
  isDeleting: string | null
}

const mockSessions: DiscoverySession[] = [
  {
    id: 'session-1',
    name: 'Q1 Discovery',
    status: 'In Progress',
    currentStep: 2,
    totalSteps: 5,
    createdAt: '2026-01-15T10:00:00Z',
    updatedAt: '2026-01-20T14:30:00Z',
  },
  {
    id: 'session-2',
    name: 'Engineering Team Analysis',
    status: 'Completed',
    currentStep: 5,
    totalSteps: 5,
    createdAt: '2025-12-01T09:00:00Z',
    updatedAt: '2025-12-15T16:45:00Z',
  },
  {
    id: 'session-3',
    name: 'HR Department Discovery',
    status: 'Draft',
    currentStep: 1,
    totalSteps: 5,
    createdAt: '2026-01-25T11:00:00Z',
    updatedAt: '2026-01-25T11:00:00Z',
  },
]

const PAGE_SIZE = 10

/**
 * Sanitizes session name by removing potentially dangerous characters
 */
function sanitizeName(name: string): string {
  return name.replace(/[<>]/g, '').trim()
}

/**
 * Validates session name
 */
function validateName(name: string): { isValid: boolean; error?: string } {
  const sanitized = sanitizeName(name)
  if (!sanitized || sanitized.length === 0) {
    return { isValid: false, error: 'Session name cannot be empty' }
  }
  return { isValid: true }
}

export function useDiscoverySessions(): UseDiscoverySessionsReturn {
  const [sessions, setSessions] = useState<DiscoverySession[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [isCreating, setIsCreating] = useState(false)
  const [isDeleting, setIsDeleting] = useState<string | null>(null)

  const fetchSessions = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)
      // Simulate API delay
      await new Promise((resolve) => setTimeout(resolve, 100))

      // Simulate pagination
      const startIndex = (page - 1) * PAGE_SIZE
      const endIndex = startIndex + PAGE_SIZE
      const paginatedSessions = mockSessions.slice(startIndex, endIndex)

      setSessions(paginatedSessions)
      setTotalPages(Math.max(1, Math.ceil(mockSessions.length / PAGE_SIZE)))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load sessions')
    } finally {
      setIsLoading(false)
    }
  }, [page])

  useEffect(() => {
    fetchSessions()
  }, [fetchSessions])

  const createSession = useCallback(async (name: string): Promise<DiscoverySession> => {
    // Validate and sanitize name
    const validation = validateName(name)
    if (!validation.isValid) {
      const error = new Error(validation.error || 'Invalid session name')
      setError(error.message)
      throw error
    }

    const sanitizedName = sanitizeName(name)

    try {
      setIsCreating(true)
      setError(null)
      // Simulate API delay
      await new Promise((resolve) => setTimeout(resolve, 200))

      const newSession: DiscoverySession = {
        id: `session-${Date.now()}`,
        name: sanitizedName,
        status: 'Draft',
        currentStep: 1,
        totalSteps: 5,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      }

      setSessions((prev) => [newSession, ...prev])
      return newSession
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create session'
      setError(errorMessage)
      throw err
    } finally {
      setIsCreating(false)
    }
  }, [])

  const deleteSession = useCallback(async (id: string): Promise<void> => {
    try {
      setIsDeleting(id)
      setError(null)
      // Simulate API delay
      await new Promise((resolve) => setTimeout(resolve, 200))

      setSessions((prev) => prev.filter((session) => session.id !== id))
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete session'
      setError(errorMessage)
      throw err
    } finally {
      setIsDeleting(null)
    }
  }, [])

  return {
    sessions,
    isLoading,
    error,
    page,
    totalPages,
    setPage,
    createSession,
    deleteSession,
    isCreating,
    isDeleting,
  }
}
