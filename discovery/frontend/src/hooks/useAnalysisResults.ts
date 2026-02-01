import { useState, useCallback, useEffect, useMemo } from 'react'

export type Dimension = 'ROLE' | 'DEPARTMENT' | 'GEOGRAPHY'
export type PriorityTier = 'HIGH' | 'MEDIUM' | 'LOW'

export interface AnalysisResult {
  id: string
  name: string
  dimension: Dimension
  exposure: number
  impact: number
  priority: number
  tier: PriorityTier
}

export interface UseAnalysisResultsReturn {
  results: AnalysisResult[]
  filteredResults: AnalysisResult[]
  isLoading: boolean
  error: string | null
  selectedDimension: Dimension
  filterTier: PriorityTier | 'ALL'
  setSelectedDimension: (dimension: Dimension) => void
  setFilterTier: (tier: PriorityTier | 'ALL') => void
  fetchResults: () => void
}

const mockResultsByDimension: Record<Dimension, AnalysisResult[]> = {
  ROLE: [
    {
      id: 'role-1',
      name: 'Software Engineer',
      dimension: 'ROLE',
      exposure: 0.75,
      impact: 0.85,
      priority: 0.80,
      tier: 'HIGH',
    },
    {
      id: 'role-2',
      name: 'Data Analyst',
      dimension: 'ROLE',
      exposure: 0.65,
      impact: 0.70,
      priority: 0.68,
      tier: 'MEDIUM',
    },
    {
      id: 'role-3',
      name: 'Customer Support',
      dimension: 'ROLE',
      exposure: 0.45,
      impact: 0.40,
      priority: 0.42,
      tier: 'LOW',
    },
  ],
  DEPARTMENT: [
    {
      id: 'dept-1',
      name: 'Engineering',
      dimension: 'DEPARTMENT',
      exposure: 0.72,
      impact: 0.78,
      priority: 0.75,
      tier: 'MEDIUM',
    },
    {
      id: 'dept-2',
      name: 'Marketing',
      dimension: 'DEPARTMENT',
      exposure: 0.55,
      impact: 0.60,
      priority: 0.58,
      tier: 'MEDIUM',
    },
  ],
  GEOGRAPHY: [
    {
      id: 'geo-1',
      name: 'North America',
      dimension: 'GEOGRAPHY',
      exposure: 0.68,
      impact: 0.72,
      priority: 0.70,
      tier: 'MEDIUM',
    },
    {
      id: 'geo-2',
      name: 'Europe',
      dimension: 'GEOGRAPHY',
      exposure: 0.62,
      impact: 0.65,
      priority: 0.64,
      tier: 'MEDIUM',
    },
  ],
}

// TODO: sessionId will be used for API calls to fetch analysis results for a specific session
export function useAnalysisResults(sessionId?: string): UseAnalysisResultsReturn {
  const [results, setResults] = useState<AnalysisResult[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedDimension, setSelectedDimension] = useState<Dimension>('ROLE')
  const [filterTier, setFilterTier] = useState<PriorityTier | 'ALL'>('ALL')

  const fetchResults = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)
      // Simulate API delay
      // TODO: Replace with actual API call using sessionId
      await new Promise((resolve) => setTimeout(resolve, 100))
      setResults(mockResultsByDimension[selectedDimension])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analysis results')
    } finally {
      setIsLoading(false)
    }
  }, [selectedDimension])

  useEffect(() => {
    fetchResults()
  }, [fetchResults])

  // Memoize filtered results to avoid recalculating on every render
  const filteredResults = useMemo(() => {
    return filterTier === 'ALL'
      ? results
      : results.filter((result) => result.tier === filterTier)
  }, [results, filterTier])

  return {
    results,
    filteredResults,
    isLoading,
    error,
    selectedDimension,
    filterTier,
    setSelectedDimension,
    setFilterTier,
    fetchResults,
  }
}
