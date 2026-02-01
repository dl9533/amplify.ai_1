import { useMemo, useCallback, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { useAnalysisResults, Dimension, PriorityTier, AnalysisResult } from '@/hooks/useAnalysisResults'

// Utility function moved outside component for performance
function formatScore(score: number): string {
  return (score * 100).toFixed(0) + '%'
}

// Constants moved outside component to avoid recreating on each render
const DIMENSIONS: { dimension: Dimension; label: string }[] = [
  { dimension: 'ROLE', label: 'Role' },
  { dimension: 'DEPARTMENT', label: 'Department' },
  { dimension: 'GEOGRAPHY', label: 'Geography' },
]

// Generic error message to prevent XSS
const GENERIC_ERROR_MESSAGE = 'An error occurred while loading analysis results. Please try again.'

interface DimensionTabProps {
  dimension: Dimension
  label: string
  isSelected: boolean
  tabIndex: number
  panelId: string
  onSelect: (dimension: Dimension) => void
  onKeyDown: (event: React.KeyboardEvent, dimension: Dimension) => void
}

function DimensionTab({ dimension, label, isSelected, tabIndex, panelId, onSelect, onKeyDown }: DimensionTabProps) {
  return (
    <button
      role="tab"
      id={`tab-${dimension}`}
      aria-selected={isSelected}
      aria-controls={panelId}
      aria-label={label}
      tabIndex={tabIndex}
      onClick={() => onSelect(dimension)}
      onKeyDown={(e) => onKeyDown(e, dimension)}
      className={`px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 transition-colors ${
        isSelected
          ? 'border-blue-600 text-blue-600 bg-blue-50'
          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
      }`}
    >
      {label}
    </button>
  )
}

interface PriorityBadgeProps {
  tier: PriorityTier
}

function PriorityBadge({ tier }: PriorityBadgeProps) {
  const colorClasses = {
    HIGH: 'bg-red-100 text-red-800',
    MEDIUM: 'bg-yellow-100 text-yellow-800',
    LOW: 'bg-green-100 text-green-800',
  }

  return (
    <span className={`px-2 py-1 text-xs font-semibold rounded ${colorClasses[tier]}`}>
      {tier}
    </span>
  )
}

interface ResultCardProps {
  result: AnalysisResult
}

function ResultCard({ result }: ResultCardProps) {
  return (
    <div className="bg-white border rounded-lg p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-medium text-gray-900">{result.name}</h3>
        <PriorityBadge tier={result.tier} />
      </div>
      <div className="grid grid-cols-3 gap-4 text-sm">
        <div>
          <span className="text-gray-500">Exposure:</span>
          <span className="ml-1 font-medium text-gray-900">{formatScore(result.exposure)}</span>
        </div>
        <div>
          <span className="text-gray-500">Impact:</span>
          <span className="ml-1 font-medium text-gray-900">{formatScore(result.impact)}</span>
        </div>
        <div>
          <span className="text-gray-500">Priority:</span>
          <span className="ml-1 font-medium text-gray-900">{formatScore(result.priority)}</span>
        </div>
      </div>
    </div>
  )
}

export function AnalysisStep() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const {
    filteredResults,
    isLoading,
    error,
    selectedDimension,
    filterTier,
    setSelectedDimension,
    setFilterTier,
  } = useAnalysisResults(sessionId)

  const tablistRef = useRef<HTMLDivElement>(null)

  // Memoize dimensions array (using constant defined outside component)
  const dimensions = useMemo(() => DIMENSIONS, [])

  const panelId = `tabpanel-${selectedDimension}`

  // Handle keyboard navigation for tabs
  const handleTabKeyDown = useCallback((event: React.KeyboardEvent, currentDimension: Dimension) => {
    const currentIndex = dimensions.findIndex(d => d.dimension === currentDimension)
    let newIndex: number | null = null

    if (event.key === 'ArrowRight') {
      event.preventDefault()
      newIndex = (currentIndex + 1) % dimensions.length
    } else if (event.key === 'ArrowLeft') {
      event.preventDefault()
      newIndex = (currentIndex - 1 + dimensions.length) % dimensions.length
    }

    if (newIndex !== null) {
      const newDimension = dimensions[newIndex].dimension
      setSelectedDimension(newDimension)
      // Focus the new tab
      const newTab = tablistRef.current?.querySelector(`#tab-${newDimension}`) as HTMLButtonElement
      newTab?.focus()
    }
  }, [dimensions, setSelectedDimension])

  if (!sessionId) {
    return (
      <div className="flex items-center justify-center p-8">
        <span className="text-red-500" role="alert">
          Error: Session ID is required. Please start a new discovery session.
        </span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center p-8">
        <span className="text-red-500" role="alert">
          {GENERIC_ERROR_MESSAGE}
        </span>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Analysis Results</h1>
        <p className="mt-2 text-gray-600">
          Review AI opportunity analysis results across different dimensions.
        </p>
      </div>

      {/* Dimension Tabs */}
      <div ref={tablistRef} className="flex gap-1 mb-6 border-b border-gray-200" role="tablist">
        {dimensions.map(({ dimension, label }) => (
          <DimensionTab
            key={dimension}
            dimension={dimension}
            label={label}
            isSelected={selectedDimension === dimension}
            tabIndex={selectedDimension === dimension ? 0 : -1}
            panelId={panelId}
            onSelect={setSelectedDimension}
            onKeyDown={handleTabKeyDown}
          />
        ))}
      </div>

      {/* Filter Controls */}
      <div className="mb-6 flex items-center gap-4">
        <label htmlFor="priority-filter" className="text-sm font-medium text-gray-700">
          Filter by priority:
        </label>
        <select
          id="priority-filter"
          aria-label="Filter by priority tier"
          value={filterTier}
          onChange={(e) => setFilterTier(e.target.value as PriorityTier | 'ALL')}
          className="block w-40 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm"
        >
          <option value="ALL">All</option>
          <option value="HIGH">HIGH</option>
          <option value="MEDIUM">MEDIUM</option>
          <option value="LOW">LOW</option>
        </select>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center p-8" role="status" aria-live="polite">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-500">Analyzing...</span>
        </div>
      )}

      {/* Results Panel */}
      {!isLoading && (
        <div
          role="tabpanel"
          id={panelId}
          aria-labelledby={`tab-${selectedDimension}`}
          className="space-y-4"
        >
          {filteredResults.map((result) => (
            <ResultCard key={result.id} result={result} />
          ))}

          {filteredResults.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No results found for the selected filters.
            </div>
          )}
        </div>
      )}
    </div>
  )
}
