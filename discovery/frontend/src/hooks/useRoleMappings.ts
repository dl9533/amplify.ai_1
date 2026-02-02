import { useState, useCallback, useEffect } from 'react'
import { roleMappingsApi, ApiError } from '../services'

export interface RoleMapping {
  id: string
  roleName: string
  onetCode: string
  onetTitle: string
  confidence: number
  confirmed: boolean
}

export interface UseRoleMappingsReturn {
  mappings: RoleMapping[]
  isLoading: boolean
  error: string | null
  confirmMapping: (id: string) => Promise<void>
  bulkConfirm: (threshold: number) => Promise<void>
  remapRole: (id: string, onetCode: string, onetTitle: string) => Promise<void>
  refresh: () => Promise<void>
}

export function useRoleMappings(sessionId?: string): UseRoleMappingsReturn {
  const [mappings, setMappings] = useState<RoleMapping[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadMappings = useCallback(async () => {
    if (!sessionId) {
      setMappings([])
      setIsLoading(false)
      return
    }

    try {
      setIsLoading(true)
      setError(null)

      const response = await roleMappingsApi.getBySession(sessionId)

      // Map API response to frontend interface
      const mappedData: RoleMapping[] = response.map((m) => ({
        id: m.id,
        roleName: m.source_role,
        onetCode: m.onet_code,
        onetTitle: m.onet_title,
        confidence: Math.round(m.confidence_score * 100),
        confirmed: m.is_confirmed,
      }))

      setMappings(mappedData)
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Failed to load role mappings'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }, [sessionId])

  useEffect(() => {
    loadMappings()
  }, [loadMappings])

  const confirmMapping = useCallback(async (id: string) => {
    // Optimistic update
    setMappings((prev) =>
      prev.map((mapping) =>
        mapping.id === id ? { ...mapping, confirmed: true } : mapping
      )
    )

    try {
      await roleMappingsApi.update(id, { is_confirmed: true })
    } catch (err) {
      // Revert on error
      setMappings((prev) =>
        prev.map((mapping) =>
          mapping.id === id ? { ...mapping, confirmed: false } : mapping
        )
      )
      const message =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Failed to confirm mapping'
      setError(message)
    }
  }, [])

  const bulkConfirm = useCallback(
    async (threshold: number) => {
      if (!sessionId) return

      // Store previous state for rollback
      const previousMappings = [...mappings]

      // Optimistic update
      setMappings((prev) =>
        prev.map((mapping) =>
          mapping.confidence >= threshold ? { ...mapping, confirmed: true } : mapping
        )
      )

      try {
        // API expects threshold as decimal (0-1)
        await roleMappingsApi.bulkConfirm(sessionId, threshold / 100)
      } catch (err) {
        // Revert on error
        setMappings(previousMappings)
        const message =
          err instanceof ApiError
            ? err.message
            : err instanceof Error
              ? err.message
              : 'Failed to bulk confirm mappings'
        setError(message)
      }
    },
    [sessionId, mappings]
  )

  const remapRole = useCallback(async (id: string, onetCode: string, onetTitle: string) => {
    // Store previous state for rollback
    const previousMapping = mappings.find((m) => m.id === id)

    // Optimistic update
    setMappings((prev) =>
      prev.map((mapping) =>
        mapping.id === id
          ? { ...mapping, onetCode, onetTitle, confidence: 100, confirmed: true }
          : mapping
      )
    )

    try {
      await roleMappingsApi.update(id, {
        onet_code: onetCode,
        onet_title: onetTitle,
        is_confirmed: true,
      })
    } catch (err) {
      // Revert on error
      if (previousMapping) {
        setMappings((prev) =>
          prev.map((mapping) => (mapping.id === id ? previousMapping : mapping))
        )
      }
      const message =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Failed to remap role'
      setError(message)
    }
  }, [mappings])

  return {
    mappings,
    isLoading,
    error,
    confirmMapping,
    bulkConfirm,
    remapRole,
    refresh: loadMappings,
  }
}
