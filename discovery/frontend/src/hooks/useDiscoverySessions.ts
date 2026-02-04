import { useState, useCallback, useEffect } from 'react'
import { sessionsApi, ApiError } from '../services'
import type { SessionStatus as ApiSessionStatus } from '../services'

export type SessionStatus = 'draft' | 'in_progress' | 'completed' | 'archived'

export interface DiscoverySession {
  id: string
  name: string
  status: SessionStatus
  currentStep: number
  totalSteps: number
  createdAt: string
  updatedAt: string
}

const PAGE_SIZE = 10

/**
 * Map API status to frontend status.
 */
function mapStatus(apiStatus: ApiSessionStatus): SessionStatus {
  switch (apiStatus) {
    case 'draft':
      return 'draft'
    case 'in_progress':
      return 'in_progress'
    case 'completed':
      return 'completed'
    default:
      return 'draft'
  }
}

export function useDiscoverySessions() {
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

      const response = await sessionsApi.list(page, PAGE_SIZE)

      // Map API response to frontend interface
      const mappedSessions: DiscoverySession[] = response.items.map((item) => ({
        id: item.id,
        name: `Session ${item.id.slice(0, 8)}`,
        status: mapStatus(item.status),
        currentStep: item.current_step,
        totalSteps: 5,
        createdAt: item.created_at,
        updatedAt: item.updated_at,
      }))

      setSessions(mappedSessions)
      setTotalPages(Math.max(1, Math.ceil(response.total / PAGE_SIZE)))
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError(err instanceof Error ? err.message : 'Failed to load sessions')
      }
    } finally {
      setIsLoading(false)
    }
  }, [page])

  useEffect(() => {
    fetchSessions()
  }, [fetchSessions])

  const createSession = useCallback(
    async (): Promise<DiscoverySession | null> => {
      try {
        setIsCreating(true)
        setError(null)

        // Use a placeholder organization ID for now
        const organizationId = '00000000-0000-0000-0000-000000000001'
        const response = await sessionsApi.create(organizationId)

        const newSession: DiscoverySession = {
          id: response.id,
          name: `Session ${response.id.slice(0, 8)}`,
          status: mapStatus(response.status),
          currentStep: response.current_step,
          totalSteps: 5,
          createdAt: response.created_at,
          updatedAt: response.updated_at,
        }

        // Optimistic update - add to beginning of list
        setSessions((prev) => [newSession, ...prev])
        return newSession
      } catch (err) {
        const errorMessage =
          err instanceof ApiError
            ? err.message
            : err instanceof Error
              ? err.message
              : 'Failed to create session'
        setError(errorMessage)
        return null
      } finally {
        setIsCreating(false)
      }
    },
    []
  )

  const deleteSession = useCallback(async (id: string): Promise<void> => {
    try {
      setIsDeleting(id)
      setError(null)

      await sessionsApi.delete(id)

      // Remove from local state
      setSessions((prev) => prev.filter((session) => session.id !== id))
    } catch (err) {
      const errorMessage =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Failed to delete session'
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
