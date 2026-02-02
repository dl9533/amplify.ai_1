import { useState, useEffect, useRef } from 'react'
import { onetApi, ApiError } from '../services'

export interface OnetOccupation {
  code: string
  title: string
}

export interface UseOnetSearchReturn {
  query: string
  setQuery: (query: string) => void
  results: OnetOccupation[]
  isLoading: boolean
  error: string | null
}

const DEBOUNCE_DELAY = 300

export function useOnetSearch(): UseOnetSearchReturn {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<OnetOccupation[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    if (!query.trim()) {
      setResults([])
      setIsLoading(false)
      setError(null)
      return
    }

    setIsLoading(true)
    setError(null)

    debounceTimerRef.current = setTimeout(async () => {
      try {
        const response = await onetApi.search(query)

        // Map API response to frontend interface
        const searchResults: OnetOccupation[] = response.map((r) => ({
          code: r.code,
          title: r.title,
        }))

        setResults(searchResults)
      } catch (err) {
        const message =
          err instanceof ApiError
            ? err.message
            : err instanceof Error
              ? err.message
              : 'Failed to search O*NET'
        setError(message)
        setResults([])
      } finally {
        setIsLoading(false)
      }
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
    error,
  }
}
