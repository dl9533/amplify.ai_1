import { useState, useCallback, useEffect } from 'react'
import {
  roleMappingsApi,
  ApiError,
  GroupedRoleMappingsResponse,
} from '../services'

export interface UseGroupedRoleMappingsReturn {
  data: GroupedRoleMappingsResponse | null
  isLoading: boolean
  isConfirming: boolean
  error: string | null
  confirmMapping: (mappingId: string) => Promise<void>
  bulkConfirmLob: (lob: string, threshold: number) => Promise<void>
  bulkConfirmAll: (threshold: number) => Promise<void>
  refresh: () => Promise<void>
}

export function useGroupedRoleMappings(sessionId?: string): UseGroupedRoleMappingsReturn {
  const [data, setData] = useState<GroupedRoleMappingsResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isConfirming, setIsConfirming] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadGroupedMappings = useCallback(async () => {
    if (!sessionId) {
      setData(null)
      setIsLoading(false)
      return
    }

    try {
      setIsLoading(true)
      setError(null)

      const response = await roleMappingsApi.getGroupedBySession(sessionId)
      setData(response)
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Failed to load grouped role mappings'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }, [sessionId])

  useEffect(() => {
    loadGroupedMappings()
  }, [loadGroupedMappings])

  const confirmMapping = useCallback(async (mappingId: string) => {
    try {
      await roleMappingsApi.update(mappingId, { is_confirmed: true })
      // Refresh to get updated data
      await loadGroupedMappings()
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Failed to confirm mapping'
      setError(message)
    }
  }, [loadGroupedMappings])

  const bulkConfirmLob = useCallback(
    async (lob: string, threshold: number) => {
      if (!sessionId) return

      try {
        setIsConfirming(true)
        setError(null)

        await roleMappingsApi.bulkConfirm(sessionId, threshold, lob)
        // Refresh to get updated data
        await loadGroupedMappings()
      } catch (err) {
        const message =
          err instanceof ApiError
            ? err.message
            : err instanceof Error
              ? err.message
              : 'Failed to bulk confirm mappings'
        setError(message)
      } finally {
        setIsConfirming(false)
      }
    },
    [sessionId, loadGroupedMappings]
  )

  const bulkConfirmAll = useCallback(
    async (threshold: number) => {
      if (!sessionId) return

      try {
        setIsConfirming(true)
        setError(null)

        await roleMappingsApi.bulkConfirm(sessionId, threshold)
        // Refresh to get updated data
        await loadGroupedMappings()
      } catch (err) {
        const message =
          err instanceof ApiError
            ? err.message
            : err instanceof Error
              ? err.message
              : 'Failed to bulk confirm mappings'
        setError(message)
      } finally {
        setIsConfirming(false)
      }
    },
    [sessionId, loadGroupedMappings]
  )

  return {
    data,
    isLoading,
    isConfirming,
    error,
    confirmMapping,
    bulkConfirmLob,
    bulkConfirmAll,
    refresh: loadGroupedMappings,
  }
}
