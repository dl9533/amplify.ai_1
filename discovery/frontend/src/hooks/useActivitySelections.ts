import { useState, useCallback, useEffect } from 'react'

export interface DWA {
  id: string
  title: string
  aiExposure: number
}

export interface GWA {
  id: string
  title: string
  aiExposure: number
  dwas: DWA[]
}

export interface UseActivitySelectionsReturn {
  gwaGroups: GWA[]
  selectedDwaIds: Set<string>
  isLoading: boolean
  error: string | null
  selectDwa: (id: string) => void
  deselectDwa: (id: string) => void
  toggleDwa: (id: string) => void
  selectHighExposure: (threshold?: number) => void
  selectionCount: number
}

const mockGwaGroups: GWA[] = [
  {
    id: 'gwa-1',
    title: 'Analyzing Data',
    aiExposure: 72,
    dwas: [
      { id: 'dwa-1-1', title: 'Analyze business data', aiExposure: 85 },
      { id: 'dwa-1-2', title: 'Interpret statistical reports', aiExposure: 78 },
      { id: 'dwa-1-3', title: 'Evaluate data quality', aiExposure: 65 },
    ],
  },
  {
    id: 'gwa-2',
    title: 'Communicating with Others',
    aiExposure: 45,
    dwas: [
      { id: 'dwa-2-1', title: 'Present information to stakeholders', aiExposure: 55 },
      { id: 'dwa-2-2', title: 'Coordinate with team members', aiExposure: 40 },
      { id: 'dwa-2-3', title: 'Negotiate contracts', aiExposure: 35 },
    ],
  },
  {
    id: 'gwa-3',
    title: 'Processing Information',
    aiExposure: 88,
    dwas: [
      { id: 'dwa-3-1', title: 'Compile data for reports', aiExposure: 92 },
      { id: 'dwa-3-2', title: 'Calculate financial metrics', aiExposure: 90 },
      { id: 'dwa-3-3', title: 'Review documents for accuracy', aiExposure: 82 },
    ],
  },
]

const HIGH_EXPOSURE_THRESHOLD = 70

export function useActivitySelections(_sessionId?: string): UseActivitySelectionsReturn {
  const [gwaGroups, setGwaGroups] = useState<GWA[]>([])
  const [selectedDwaIds, setSelectedDwaIds] = useState<Set<string>>(new Set())
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadActivities = async () => {
      try {
        setIsLoading(true)
        setError(null)
        // Simulate API delay
        await new Promise((resolve) => setTimeout(resolve, 100))
        setGwaGroups(mockGwaGroups)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load activities')
      } finally {
        setIsLoading(false)
      }
    }
    loadActivities()
  }, [_sessionId])

  const selectDwa = useCallback((id: string) => {
    setSelectedDwaIds((prev) => {
      const next = new Set(prev)
      next.add(id)
      return next
    })
  }, [])

  const deselectDwa = useCallback((id: string) => {
    setSelectedDwaIds((prev) => {
      const next = new Set(prev)
      next.delete(id)
      return next
    })
  }, [])

  const toggleDwa = useCallback((id: string) => {
    setSelectedDwaIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }, [])

  const selectHighExposure = useCallback((threshold: number = HIGH_EXPOSURE_THRESHOLD) => {
    const highExposureDwaIds: string[] = []
    for (const gwa of gwaGroups) {
      for (const dwa of gwa.dwas) {
        if (dwa.aiExposure >= threshold) {
          highExposureDwaIds.push(dwa.id)
        }
      }
    }
    setSelectedDwaIds((prev) => {
      const next = new Set(prev)
      for (const id of highExposureDwaIds) {
        next.add(id)
      }
      return next
    })
  }, [gwaGroups])

  return {
    gwaGroups,
    selectedDwaIds,
    isLoading,
    error,
    selectDwa,
    deselectDwa,
    toggleDwa,
    selectHighExposure,
    selectionCount: selectedDwaIds.size,
  }
}
