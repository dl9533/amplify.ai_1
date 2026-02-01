import { useState, useCallback, useEffect } from 'react'

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
  confirmMapping: (id: string) => void
  bulkConfirm: (threshold: number) => void
  remapRole: (id: string, onetCode: string, onetTitle: string) => void
}

const mockMappings: RoleMapping[] = [
  {
    id: '1',
    roleName: 'Software Engineer',
    onetCode: '15-1252.00',
    onetTitle: 'Software Developers',
    confidence: 95,
    confirmed: false,
  },
  {
    id: '2',
    roleName: 'Data Analyst',
    onetCode: '15-2051.00',
    onetTitle: 'Data Scientists',
    confidence: 87,
    confirmed: false,
  },
  {
    id: '3',
    roleName: 'Project Manager',
    onetCode: '11-9199.00',
    onetTitle: 'Project Management Specialists',
    confidence: 78,
    confirmed: false,
  },
]

export function useRoleMappings(_sessionId?: string): UseRoleMappingsReturn {
  const [mappings, setMappings] = useState<RoleMapping[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Simulate initial loading state
    const loadMappings = async () => {
      try {
        setIsLoading(true)
        setError(null)
        // Simulate API delay
        await new Promise((resolve) => setTimeout(resolve, 100))
        setMappings(mockMappings)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load role mappings')
      } finally {
        setIsLoading(false)
      }
    }
    loadMappings()
  }, [_sessionId])

  const confirmMapping = useCallback((id: string) => {
    try {
      setMappings((prev) =>
        prev.map((mapping) =>
          mapping.id === id ? { ...mapping, confirmed: true } : mapping
        )
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to confirm mapping')
    }
  }, [])

  const bulkConfirm = useCallback((threshold: number) => {
    try {
      setMappings((prev) =>
        prev.map((mapping) =>
          mapping.confidence >= threshold ? { ...mapping, confirmed: true } : mapping
        )
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to bulk confirm mappings')
    }
  }, [])

  const remapRole = useCallback((id: string, onetCode: string, onetTitle: string) => {
    try {
      setMappings((prev) =>
        prev.map((mapping) =>
          mapping.id === id
            ? { ...mapping, onetCode, onetTitle, confidence: 100, confirmed: true }
            : mapping
        )
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remap role')
    }
  }, [])

  return {
    mappings,
    isLoading,
    error,
    confirmMapping,
    bulkConfirm,
    remapRole,
  }
}
