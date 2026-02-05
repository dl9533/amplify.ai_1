import { useState, useCallback, useEffect } from 'react'
import { roadmapApi, handoffApi, ApiError } from '../services'
import type { RoadmapPhase as ApiPhase } from '../services'

export type Phase = 'NOW' | 'NEXT' | 'LATER'
export type PriorityTier = 'HIGH' | 'MEDIUM' | 'LOW'

export interface RoadmapItem {
  id: string
  roleName: string
  phase: Phase
  priorityScore: number
  priorityTier: PriorityTier
  estimatedEffort: 'low' | 'medium' | 'high'
}

export function useRoadmap(sessionId: string) {
  const [items, setItems] = useState<RoadmapItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isHandingOff, setIsHandingOff] = useState(false)

  const fetchItems = useCallback(async () => {
    if (!sessionId) {
      setItems([])
      setIsLoading(false)
      return
    }

    try {
      setIsLoading(true)
      setError(null)

      const response = await roadmapApi.get(sessionId)

      // Map API response to frontend interface
      const mappedItems: RoadmapItem[] = response.items.map((item) => ({
        id: item.id,
        roleName: item.role_name,
        phase: item.phase as Phase,
        priorityScore: item.priority_score,
        priorityTier: item.priority_tier,
        estimatedEffort: (item.estimated_effort || 'medium') as 'low' | 'medium' | 'high',
      }))

      setItems(mappedItems)
    } catch (err) {
      // If roadmap hasn't been generated yet, show empty list
      if (err instanceof ApiError && err.status === 404) {
        setItems([])
        setError(null)
      } else {
        const message =
          err instanceof ApiError
            ? err.message
            : err instanceof Error
              ? err.message
              : 'Failed to load roadmap'
        setError(message)
      }
    } finally {
      setIsLoading(false)
    }
  }, [sessionId])

  useEffect(() => {
    fetchItems()
  }, [fetchItems])

  const updatePhase = useCallback(
    async (id: string, newPhase: Phase) => {
      // Store previous state for rollback
      const previousItem = items.find((item) => item.id === id)

      // Optimistic update
      setItems((prev) =>
        prev.map((item) =>
          item.id === id ? { ...item, phase: newPhase } : item
        )
      )

      try {
        await roadmapApi.updatePhase(id, newPhase as ApiPhase)
      } catch (err) {
        // Revert on error
        if (previousItem) {
          setItems((prev) =>
            prev.map((item) =>
              item.id === id ? previousItem : item
            )
          )
        }
        const message =
          err instanceof ApiError
            ? err.message
            : err instanceof Error
              ? err.message
              : 'Failed to update phase'
        setError(message)
      }
    },
    [items]
  )

  const handoff = useCallback(
    async (candidateIds: string[], notes?: string) => {
      if (!sessionId) return

      try {
        setIsHandingOff(true)
        setError(null)

        // First validate readiness
        const validation = await handoffApi.validate(sessionId)

        if (!validation.is_ready && validation.errors.length > 0) {
          throw new Error(validation.errors.join('; '))
        }

        // Submit handoff
        await handoffApi.submit(sessionId, candidateIds, notes)
      } catch (err) {
        const message =
          err instanceof ApiError
            ? err.message
            : err instanceof Error
              ? err.message
              : 'Failed to handoff'
        setError(message)
        throw err
      } finally {
        setIsHandingOff(false)
      }
    },
    [sessionId]
  )

  return {
    items,
    isLoading,
    error,
    updatePhase,
    handoff,
    isHandingOff,
  }
}
