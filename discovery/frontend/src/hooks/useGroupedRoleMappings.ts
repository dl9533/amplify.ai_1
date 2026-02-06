import { useState, useCallback, useEffect, useRef } from 'react'
import {
  roleMappingsApi,
  ApiError,
  GroupedRoleMappingsResponse,
} from '../services'

export interface UseGroupedRoleMappingsReturn {
  data: GroupedRoleMappingsResponse | null
  isLoading: boolean
  isGenerating: boolean
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
  const [isGenerating, setIsGenerating] = useState(false)
  const [isConfirming, setIsConfirming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const hasAttemptedGeneration = useRef(false)

  const generateMappings = useCallback(async () => {
    if (!sessionId) return

    try {
      setIsGenerating(true)
      setError(null)

      await roleMappingsApi.generateMappings(sessionId)
      // After generation, reload the grouped data
      const response = await roleMappingsApi.getGroupedBySession(sessionId)
      setData(response)
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Failed to generate role mappings'
      setError(message)
    } finally {
      setIsGenerating(false)
    }
  }, [sessionId])

  const loadGroupedMappings = useCallback(async (showLoading = true) => {
    if (!sessionId) {
      setData(null)
      setIsLoading(false)
      return
    }

    try {
      // Only show loading spinner on initial load, not on refreshes
      if (showLoading) {
        setIsLoading(true)
      }
      setError(null)

      const response = await roleMappingsApi.getGroupedBySession(sessionId)

      // If no mappings exist and we haven't tried generating yet, auto-generate
      if (response.overall_summary.total_roles === 0 && !hasAttemptedGeneration.current) {
        hasAttemptedGeneration.current = true
        setIsLoading(false)
        await generateMappings()
        return
      }

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
  }, [sessionId, generateMappings])

  useEffect(() => {
    // Reset generation attempt flag when session changes
    hasAttemptedGeneration.current = false
    loadGroupedMappings()
  }, [loadGroupedMappings])

  const confirmMapping = useCallback(async (mappingId: string) => {
    try {
      await roleMappingsApi.update(mappingId, { is_confirmed: true })
      // Refresh to get updated data without showing loading spinner
      await loadGroupedMappings(false)
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
        // Refresh to get updated data without showing loading spinner
        await loadGroupedMappings(false)
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
        // Refresh to get updated data without showing loading spinner
        await loadGroupedMappings(false)
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
    isGenerating,
    isConfirming,
    error,
    confirmMapping,
    bulkConfirmLob,
    bulkConfirmAll,
    refresh: loadGroupedMappings,
  }
}
