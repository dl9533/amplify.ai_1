import { useState, useCallback, useEffect, useRef } from 'react'
import { analysisApi, ApiError } from '../services'
import type { AnalysisDimension as ApiDimension, PriorityTier as ApiTier } from '../services'

export type Dimension = 'role' | 'department' | 'geography' | 'lob'
export type PriorityTier = 'HIGH' | 'MEDIUM' | 'LOW'

export interface AnalysisResult {
  id: string
  name: string
  roleMappingId?: string  // For drill-down navigation (role dimension only)
  dimension: Dimension
  exposure: number
  impact: number
  priority: number
  tier: PriorityTier
  rowCount?: number
}

/**
 * Map API tier to frontend tier.
 */
function fromApiTier(tier: ApiTier): PriorityTier {
  return tier as PriorityTier
}

export function useAnalysisResults(
  sessionId: string,
  dimension: Dimension = 'role',
  tier?: PriorityTier
) {
  const [results, setResults] = useState<AnalysisResult[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [warnings, setWarnings] = useState<string[]>([])
  const [isTriggering, setIsTriggering] = useState(false)

  // Track the current fetch request version to prevent stale updates
  const fetchVersionRef = useRef(0)

  const fetchResults = useCallback(async () => {
    if (!sessionId) {
      setResults([])
      setIsLoading(false)
      return
    }

    // Increment version to track this request
    const currentVersion = ++fetchVersionRef.current

    try {
      setIsLoading(true)
      setError(null)

      const response = await analysisApi.getByDimension(
        sessionId,
        dimension as ApiDimension,
        tier as ApiTier | undefined
      )

      // Only update state if this is still the most recent request
      // This prevents race conditions when dimension/tier changes rapidly
      if (currentVersion !== fetchVersionRef.current) {
        return // Stale request, ignore results
      }

      // Map API response to frontend interface
      const mappedResults: AnalysisResult[] = response.results.map((r) => ({
        id: r.id,
        name: r.name,
        roleMappingId: r.role_mapping_id,
        dimension: dimension,
        exposure: r.ai_exposure_score,
        impact: r.impact_score,
        priority: r.priority_score,
        tier: fromApiTier(r.priority_tier),
        rowCount: r.row_count,
      }))

      setResults(mappedResults)
    } catch (err) {
      // Only handle errors for the current request
      if (currentVersion !== fetchVersionRef.current) {
        return // Stale request, ignore error
      }

      // If analysis hasn't been run yet, show empty results instead of error
      if (err instanceof ApiError && err.status === 404) {
        setResults([])
        setError(null)
      } else {
        const message =
          err instanceof ApiError
            ? err.message
            : err instanceof Error
              ? err.message
              : 'Failed to load analysis results'
        setError(message)
      }
    } finally {
      // Only clear loading for the current request
      if (currentVersion === fetchVersionRef.current) {
        setIsLoading(false)
      }
    }
  }, [sessionId, dimension, tier])

  useEffect(() => {
    fetchResults()
  }, [fetchResults])

  const triggerAnalysis = useCallback(async () => {
    if (!sessionId) return

    try {
      setIsTriggering(true)
      setError(null)
      setWarnings([])

      const response = await analysisApi.trigger(sessionId)

      // Capture any warnings from the response
      if (response.warnings && response.warnings.length > 0) {
        setWarnings(response.warnings)
      }

      // Refresh results after triggering analysis
      await fetchResults()
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Failed to trigger analysis'
      setError(message)
    } finally {
      setIsTriggering(false)
    }
  }, [sessionId, fetchResults])

  return {
    results,
    isLoading,
    error,
    warnings,
    triggerAnalysis,
    isTriggering,
    clearWarnings: () => setWarnings([]),
  }
}
