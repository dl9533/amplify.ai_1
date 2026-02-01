import { useState, useEffect, useRef } from 'react'

export interface OnetOccupation {
  code: string
  title: string
}

export interface UseOnetSearchReturn {
  query: string
  setQuery: (query: string) => void
  results: OnetOccupation[]
  isLoading: boolean
}

// Mock data for search results
const mockOccupations: OnetOccupation[] = [
  { code: '15-1252.00', title: 'Software Developers' },
  { code: '15-1253.00', title: 'Software Quality Assurance Analysts and Testers' },
  { code: '15-1254.00', title: 'Web Developers' },
  { code: '15-1255.00', title: 'Web and Digital Interface Designers' },
  { code: '15-1211.00', title: 'Computer Systems Analysts' },
]

const DEBOUNCE_DELAY = 300

export function useOnetSearch(): UseOnetSearchReturn {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<OnetOccupation[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    if (!query.trim()) {
      setResults([])
      setIsLoading(false)
      return
    }

    setIsLoading(true)

    debounceTimerRef.current = setTimeout(() => {
      // Mock search - filter occupations that match the query
      const searchQuery = query.toLowerCase()
      const filteredResults = mockOccupations.filter(
        (occupation) =>
          occupation.title.toLowerCase().includes(searchQuery) ||
          occupation.code.toLowerCase().includes(searchQuery)
      )
      setResults(filteredResults)
      setIsLoading(false)
    }, DEBOUNCE_DELAY)

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
    }
  }, [query])

  return {
    query,
    setQuery,
    results,
    isLoading,
  }
}
