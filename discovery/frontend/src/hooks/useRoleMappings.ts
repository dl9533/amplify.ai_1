import { useState, useCallback, useEffect, useRef } from 'react'
import { roleMappingsApi, ApiError, ConfidenceTier } from '../services'

export interface RoleMapping {
  id: string
  roleName: string
  onetCode: string | null
  onetTitle: string | null
  confidence: number
  confidenceTier?: ConfidenceTier
  reasoning?: string
  confirmed: boolean
  rowCount?: number
}

export interface UseRoleMappingsReturn {
  mappings: RoleMapping[]
  isLoading: boolean
  isGenerating: boolean
  isRemapping: boolean
  error: string | null
  confirmMapping: (id: string) => Promise<void>
  bulkConfirm: (threshold: number) => Promise<void>
  bulkRemap: (threshold?: number, mappingIds?: string[]) => Promise<void>
  remapRole: (id: string, onetCode: string, onetTitle: string) => Promise<void>
  generateMappings: () => Promise<void>
  refresh: () => Promise<void>
}

export function useRoleMappings(sessionId?: string): UseRoleMappingsReturn {
  const [mappings, setMappings] = useState<RoleMapping[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isRemapping, setIsRemapping] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const hasAttemptedGeneration = useRef(false)

  const generateMappings = useCallback(async () => {
    if (!sessionId) return

    try {
      setIsGenerating(true)
      setError(null)

      const response = await roleMappingsApi.generateMappings(sessionId)

      // Map the created mappings to frontend interface
      const mappedData: RoleMapping[] = response.mappings.map((m) => ({
        id: m.id,
        roleName: m.source_role,
        onetCode: m.onet_code,
        onetTitle: m.onet_title,
        confidence: m.confidence_score,
        confidenceTier: m.confidence_tier,
        reasoning: m.reasoning || undefined,
        confirmed: m.is_confirmed,
      }))

      setMappings(mappedData)
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
        confidence: m.confidence_score, // Keep as decimal 0-1
        confidenceTier: m.confidence_tier,
        reasoning: m.reasoning,
        confirmed: m.is_confirmed,
        rowCount: m.row_count,
      }))

      // If no mappings exist and we haven't tried generating yet, auto-generate
      if (mappedData.length === 0 && !hasAttemptedGeneration.current) {
        hasAttemptedGeneration.current = true
        setIsLoading(false)
        await generateMappings()
        return
      }

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
  }, [sessionId, generateMappings])

  useEffect(() => {
    // Reset generation attempt flag when session changes
    hasAttemptedGeneration.current = false
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

      // Optimistic update (confidence is now decimal 0-1)
      const decimalThreshold = threshold > 1 ? threshold / 100 : threshold
      setMappings((prev) =>
        prev.map((mapping) =>
          mapping.confidence >= decimalThreshold ? { ...mapping, confirmed: true } : mapping
        )
      )

      try {
        // API expects threshold as decimal (0-1)
        await roleMappingsApi.bulkConfirm(sessionId, decimalThreshold)
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
          ? { ...mapping, onetCode, onetTitle, confidence: 1, confirmed: true }
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

  const bulkRemap = useCallback(
    async (threshold?: number, mappingIds?: string[]) => {
      if (!sessionId) return

      try {
        setIsRemapping(true)
        setError(null)

        const result = await roleMappingsApi.bulkRemap(sessionId, threshold, mappingIds)

        // Update mappings with new results
        setMappings((prev) =>
          prev.map((mapping) => {
            const updated = result.mappings.find((m) => m.id === mapping.id)
            if (updated) {
              return {
                ...mapping,
                onetCode: updated.onet_code,
                onetTitle: updated.onet_title,
                confidence: updated.confidence_score,
                confidenceTier: updated.confidence_tier,
                reasoning: updated.reasoning || undefined,
                confirmed: updated.is_confirmed,
              }
            }
            return mapping
          })
        )
      } catch (err) {
        const message =
          err instanceof ApiError
            ? err.message
            : err instanceof Error
              ? err.message
              : 'Failed to remap roles'
        setError(message)
      } finally {
        setIsRemapping(false)
      }
    },
    [sessionId]
  )

  return {
    mappings,
    isLoading,
    isGenerating,
    isRemapping,
    error,
    confirmMapping,
    bulkConfirm,
    bulkRemap,
    remapRole,
    generateMappings,
    refresh: loadMappings,
  }
}
