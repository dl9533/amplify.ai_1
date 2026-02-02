import { useState, useCallback, useEffect } from 'react'
import { activitiesApi, ApiError } from '../services'

export interface DWA {
  id: string
  title: string
  description?: string
  aiExposure: number
}

export interface GWA {
  id: string
  title: string
  aiExposure: number
  dwas: DWA[]
}

export function useActivitySelections(sessionId: string) {
  const [activities, setActivities] = useState<GWA[]>([])
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadActivities = useCallback(async () => {
    if (!sessionId) {
      setActivities([])
      setSelectedIds(new Set())
      setIsLoading(false)
      return
    }

    try {
      setIsLoading(true)
      setError(null)

      const response = await activitiesApi.getBySession(sessionId)

      // Map API response to frontend interface
      const mappedGroups: GWA[] = response.map((gwa) => ({
        id: gwa.gwa_code,
        title: gwa.gwa_title,
        aiExposure: gwa.ai_exposure_score ?? 0,
        dwas: gwa.dwas.map((dwa) => ({
          id: dwa.id,
          title: dwa.title,
          description: dwa.description,
          aiExposure: gwa.ai_exposure_score ?? 0, // Use GWA level exposure
        })),
      }))

      // Build selected IDs set from backend data
      const newSelectedIds = new Set<string>()
      response.forEach((gwa) => {
        gwa.dwas.forEach((dwa) => {
          if (dwa.selected) {
            newSelectedIds.add(dwa.id)
          }
        })
      })

      setActivities(mappedGroups)
      setSelectedIds(newSelectedIds)
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Failed to load activities'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }, [sessionId])

  useEffect(() => {
    loadActivities()
  }, [loadActivities])

  const toggleDwa = useCallback(
    async (id: string) => {
      const isCurrentlySelected = selectedIds.has(id)

      // Optimistic update
      setSelectedIds((prev) => {
        const next = new Set(prev)
        if (isCurrentlySelected) {
          next.delete(id)
        } else {
          next.add(id)
        }
        return next
      })

      try {
        await activitiesApi.updateSelection(id, !isCurrentlySelected)
      } catch (err) {
        // Revert on error
        setSelectedIds((prev) => {
          const next = new Set(prev)
          if (isCurrentlySelected) {
            next.add(id)
          } else {
            next.delete(id)
          }
          return next
        })
        const message =
          err instanceof ApiError
            ? err.message
            : err instanceof Error
              ? err.message
              : 'Failed to update activity selection'
        setError(message)
      }
    },
    [selectedIds]
  )

  const bulkSelectByExposure = useCallback(
    async (threshold: number = 0.7) => {
      if (!sessionId) return

      // Find all DWA IDs that should be selected based on GWA exposure
      const highExposureDwaIds: string[] = []
      for (const gwa of activities) {
        if (gwa.aiExposure >= threshold) {
          for (const dwa of gwa.dwas) {
            if (!selectedIds.has(dwa.id)) {
              highExposureDwaIds.push(dwa.id)
            }
          }
        }
      }

      if (highExposureDwaIds.length === 0) return

      // Optimistic update
      setSelectedIds((prev) => {
        const next = new Set(prev)
        for (const id of highExposureDwaIds) {
          next.add(id)
        }
        return next
      })

      try {
        await activitiesApi.bulkSelect(sessionId, highExposureDwaIds, true)
      } catch (err) {
        // Revert on error
        setSelectedIds((prev) => {
          const next = new Set(prev)
          for (const id of highExposureDwaIds) {
            next.delete(id)
          }
          return next
        })
        const message =
          err instanceof ApiError
            ? err.message
            : err instanceof Error
              ? err.message
              : 'Failed to bulk select activities'
        setError(message)
      }
    },
    [sessionId, activities, selectedIds]
  )

  return {
    activities,
    selectedIds,
    isLoading,
    error,
    toggleDwa,
    bulkSelectByExposure,
  }
}
