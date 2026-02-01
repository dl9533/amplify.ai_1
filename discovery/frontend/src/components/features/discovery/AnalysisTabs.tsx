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
  const sortedResults = sortByPriority(currentResults)

  return (
    <div className="flex flex-col">
      <div role="tablist" aria-label="Analysis dimensions" className="flex border-b border-gray-200">
        {dimensions.map((dimension) => {
          const isActive = dimension === currentDimension
          const count = results[dimension]?.length ?? 0
          const label = `${formatDimensionLabel(dimension)} (${count})`

          return (
            <button
              key={dimension}
              role="tab"
              aria-selected={isActive}
              aria-controls={`tabpanel-${dimension}`}
              onClick={() => onDimensionChange(dimension)}
              className={`px-4 py-2 text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                isActive
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
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
          <div className="rounded-lg bg-gray-50 p-8 text-center">
            <p className="text-gray-500">No results found for this dimension.</p>
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
