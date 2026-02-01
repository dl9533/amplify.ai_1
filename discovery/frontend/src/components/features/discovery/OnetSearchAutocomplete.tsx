import { useState, useCallback, KeyboardEvent } from 'react'
import { useOnetSearch, OnetOccupation } from '@/hooks/useOnetSearch'

export interface OnetSearchAutocompleteProps {
  onSelect: (occupation: OnetOccupation) => void
  placeholder?: string
}

export function OnetSearchAutocomplete({
  onSelect,
  placeholder = 'Search O*NET occupations...',
}: OnetSearchAutocompleteProps) {
  const { query, setQuery, results, isLoading } = useOnetSearch()
  const [activeIndex, setActiveIndex] = useState<number>(-1)

  const handleSelect = useCallback((occupation: OnetOccupation) => {
    onSelect(occupation)
    setQuery('')
    setActiveIndex(-1)
  }, [onSelect, setQuery])

  const showDropdown = query.trim().length > 0 && !isLoading

  const handleKeyDown = useCallback((e: KeyboardEvent<HTMLInputElement>) => {
    if (!showDropdown || results.length === 0) {
      if (e.key === 'Escape') {
        setQuery('')
        setActiveIndex(-1)
      }
      return
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setActiveIndex((prev) => (prev < results.length - 1 ? prev + 1 : 0))
        break
      case 'ArrowUp':
        e.preventDefault()
        setActiveIndex((prev) => (prev > 0 ? prev - 1 : results.length - 1))
        break
      case 'Enter':
        e.preventDefault()
        if (activeIndex >= 0 && activeIndex < results.length) {
          handleSelect(results[activeIndex])
        }
        break
      case 'Escape':
        e.preventDefault()
        setQuery('')
        setActiveIndex(-1)
        break
    }
  }, [showDropdown, results, activeIndex, handleSelect, setQuery])

  const activeDescendant = activeIndex >= 0 ? `onet-option-${activeIndex}` : undefined

  return (
    <div className="relative w-full">
      <input
        type="text"
        role="combobox"
        aria-expanded={showDropdown}
        aria-controls="onet-search-listbox"
        aria-autocomplete="list"
        aria-label={placeholder || 'Search O*NET occupations'}
        aria-activedescendant={activeDescendant}
        className="w-full rounded-md border border-gray-300 px-4 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        placeholder={placeholder}
        value={query}
        onChange={(e) => {
          setQuery(e.target.value)
          setActiveIndex(-1)
        }}
        onKeyDown={handleKeyDown}
      />

      {isLoading && (
        <div
          role="status"
          aria-live="polite"
          className="absolute right-3 top-1/2 -translate-y-1/2"
        >
          <svg
            className="h-5 w-5 animate-spin text-gray-400"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          <span className="sr-only">Loading...</span>
        </div>
      )}

      {showDropdown && (
        <ul
          id="onet-search-listbox"
          role="listbox"
          className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md border border-gray-200 bg-white shadow-lg"
        >
          {results.length === 0 ? (
            <li className="px-4 py-2 text-gray-500">No results found</li>
          ) : (
            results.map((occupation, index) => (
              <li
                key={occupation.code}
                id={`onet-option-${index}`}
                role="option"
                aria-selected={activeIndex === index}
                className={`cursor-pointer px-4 py-2 ${
                  activeIndex === index ? 'bg-blue-100' : 'hover:bg-blue-50'
                }`}
                onClick={() => handleSelect(occupation)}
              >
                <div className="font-medium">{occupation.title}</div>
                <div className="text-sm text-gray-500">{occupation.code}</div>
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  )
}
