import { useState, useCallback, useEffect } from 'react'

export type Phase = 'NOW' | 'NEXT' | 'LATER'

export interface RoadmapCandidate {
  id: string
  name: string
  phase: Phase
  priorityScore: number
  exposureScore: number
}

export interface UseRoadmapReturn {
  candidates: RoadmapCandidate[]
  isLoading: boolean
  error: string | null
  updatePhase: (id: string, newPhase: Phase) => void
  handoff: () => Promise<void>
  isHandingOff: boolean
  handoffError: string | null
}

const mockCandidates: RoadmapCandidate[] = [
  {
    id: 'candidate-1',
    name: 'Software Engineer',
    phase: 'NOW',
    priorityScore: 0.92,
    exposureScore: 0.85,
  },
  {
    id: 'candidate-2',
    name: 'Data Analyst',
    phase: 'NEXT',
    priorityScore: 0.78,
    exposureScore: 0.72,
  },
  {
    id: 'candidate-3',
    name: 'Product Manager',
    phase: 'LATER',
    priorityScore: 0.65,
    exposureScore: 0.58,
  },
]

// TODO: sessionId will be used for API calls to fetch roadmap data for a specific session
export function useRoadmap(sessionId?: string): UseRoadmapReturn {
  const [candidates, setCandidates] = useState<RoadmapCandidate[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isHandingOff, setIsHandingOff] = useState(false)
  const [handoffError, setHandoffError] = useState<string | null>(null)

  const fetchCandidates = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)
      // Simulate API delay
      // TODO: Replace with actual API call using sessionId
      await new Promise((resolve) => setTimeout(resolve, 100))
      setCandidates(mockCandidates)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load roadmap candidates')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchCandidates()
  }, [fetchCandidates])

  const updatePhase = useCallback((id: string, newPhase: Phase) => {
    setCandidates((prev) =>
      prev.map((candidate) =>
        candidate.id === id ? { ...candidate, phase: newPhase } : candidate
      )
    )
  }, [])

  const handoff = useCallback(async () => {
    try {
      setIsHandingOff(true)
      setHandoffError(null)
      // Simulate API delay for handoff
      // TODO: Replace with actual API call to send to intake
      await new Promise((resolve) => setTimeout(resolve, 500))
      // Success - could navigate or update state here
    } catch (err) {
      setHandoffError(err instanceof Error ? err.message : 'Failed to handoff to intake')
      throw err
    } finally {
      setIsHandingOff(false)
    }
  }, [])

  return {
    candidates,
    isLoading,
    error,
    updatePhase,
    handoff,
    isHandingOff,
    handoffError,
  }
}
