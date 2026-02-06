import { useState, useCallback, useEffect } from 'react'
import { industryApi, sessionsApi, ApiError, Supersector } from '../services'

export interface UseIndustryReturn {
  /**
   * List of supersectors with their NAICS sectors.
   */
  supersectors: Supersector[]
  /**
   * Currently selected NAICS sector code for the session.
   */
  selectedSector: string | null
  /**
   * Whether industry list is loading.
   */
  isLoading: boolean
  /**
   * Whether a save is in progress.
   */
  isSaving: boolean
  /**
   * Error message, if any.
   */
  error: string | null
  /**
   * Update the session's industry.
   */
  updateIndustry: (naicsSector: string) => Promise<void>
  /**
   * Refresh the industry list.
   */
  refresh: () => Promise<void>
}

export function useIndustry(sessionId: string | undefined): UseIndustryReturn {
  const [supersectors, setSupersectors] = useState<Supersector[]>([])
  const [selectedSector, setSelectedSector] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load industry list and session data
  const loadData = useCallback(async () => {
    if (!sessionId) {
      setIsLoading(false)
      return
    }

    try {
      setIsLoading(true)
      setError(null)

      // Load both in parallel
      const [industriesResponse, sessionResponse] = await Promise.all([
        industryApi.list(),
        sessionsApi.get(sessionId),
      ])

      setSupersectors(industriesResponse.supersectors)
      setSelectedSector(sessionResponse.industry_naics_sector)
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Failed to load industry data'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }, [sessionId])

  useEffect(() => {
    loadData()
  }, [loadData])

  // Update industry for session
  const updateIndustry = useCallback(
    async (naicsSector: string) => {
      if (!sessionId) return

      try {
        setIsSaving(true)
        setError(null)

        const response = await sessionsApi.updateIndustry(sessionId, naicsSector)
        setSelectedSector(response.industry_naics_sector)
      } catch (err) {
        const message =
          err instanceof ApiError
            ? err.message
            : err instanceof Error
              ? err.message
              : 'Failed to update industry'
        setError(message)
        throw err
      } finally {
        setIsSaving(false)
      }
    },
    [sessionId]
  )

  return {
    supersectors,
    selectedSector,
    isLoading,
    isSaving,
    error,
    updateIndustry,
    refresh: loadData,
  }
}
