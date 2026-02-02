import { useMemo, useCallback, useRef, KeyboardEvent } from 'react'
import { AnalysisResultCard, AnalysisResult } from './AnalysisResultCard'

export type AnalysisResults = Record<string, AnalysisResult[]>

export interface AnalysisTabsProps {
  results: AnalysisResults
  activeDimension?: string
  onDimensionChange: (dimension: string) => void
}

function formatDimensionLabel(dimension: string): string {
  return dimension.charAt(0).toUpperCase() + dimension.slice(1).toLowerCase()
}

function sortByPriority(results: AnalysisResult[]): AnalysisResult[] {
  return [...results].sort((a, b) => {
    const scoreA = a.priorityScore ?? 0
    const scoreB = b.priorityScore ?? 0
    return scoreB - scoreA
  })
}

export function AnalysisTabs({
  results,
  activeDimension,
  onDimensionChange,
}: AnalysisTabsProps) {
  const dimensions = Object.keys(results)
  const currentDimension = activeDimension ?? dimensions[0]
  const currentResults = results[currentDimension] ?? []
  const tabRefs = useRef<Map<string, HTMLButtonElement>>(new Map())

  const sortedResults = useMemo(
    () => sortByPriority(currentResults),
    [currentResults, currentDimension]
  )

  const handleKeyDown = useCallback(
    (event: KeyboardEvent<HTMLButtonElement>, dimension: string) => {
      const currentIndex = dimensions.indexOf(dimension)
      let newIndex: number | null = null

      if (event.key === 'ArrowRight') {
        newIndex = (currentIndex + 1) % dimensions.length
      } else if (event.key === 'ArrowLeft') {
        newIndex = (currentIndex - 1 + dimensions.length) % dimensions.length
      }

      if (newIndex !== null) {
        event.preventDefault()
        const newDimension = dimensions[newIndex]
        onDimensionChange(newDimension)
        tabRefs.current.get(newDimension)?.focus()
      }
    },
    [dimensions, onDimensionChange]
  )

  return (
    <div className="flex flex-col">
      <div role="tablist" aria-label="Analysis dimensions" className="flex border-b border-border">
        {dimensions.map((dimension) => {
          const isActive = dimension === currentDimension
          const count = results[dimension]?.length ?? 0
          const label = `${formatDimensionLabel(dimension)} (${count})`

          return (
            <button
              key={dimension}
              ref={(el) => {
                if (el) {
                  tabRefs.current.set(dimension, el)
                } else {
                  tabRefs.current.delete(dimension)
                }
              }}
              id={`tab-${dimension}`}
              role="tab"
              aria-selected={isActive}
              aria-controls={`tabpanel-${dimension}`}
              tabIndex={isActive ? 0 : -1}
              onClick={() => onDimensionChange(dimension)}
              onKeyDown={(e) => handleKeyDown(e, dimension)}
              className={`px-4 py-2 text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background ${
                isActive
                  ? 'border-b-2 border-primary text-primary'
                  : 'text-foreground-muted hover:text-foreground'
              }`}
            >
              {label}
            </button>
          )
        })}
      </div>

      <div
        id={`tabpanel-${currentDimension}`}
        role="tabpanel"
        aria-labelledby={`tab-${currentDimension}`}
        className="mt-4"
      >
        {sortedResults.length === 0 ? (
          <div className="rounded-lg bg-background-muted p-8 text-center">
            <p className="text-foreground-muted">
              No results found for {formatDimensionLabel(currentDimension)}.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {sortedResults.map((result) => (
              <AnalysisResultCard key={result.id} result={result} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
