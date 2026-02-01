import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useActivitySelections, GWA } from '@/hooks/useActivitySelections'

interface GwaAccordionProps {
  gwa: GWA
  isExpanded: boolean
  onToggleExpand: () => void
  selectedDwaIds: Set<string>
  onToggleDwa: (id: string) => void
}

function GwaAccordion({
  gwa,
  isExpanded,
  onToggleExpand,
  selectedDwaIds,
  onToggleDwa,
}: GwaAccordionProps) {
  return (
    <div className="border rounded-lg bg-white overflow-hidden">
      <button
        onClick={onToggleExpand}
        className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-inset"
        aria-expanded={isExpanded}
      >
        <div className="flex-1">
          <h3 className="font-medium text-gray-900">{gwa.title}</h3>
          <p className="text-sm text-gray-500">{gwa.dwas.length} activities</p>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-blue-600">{gwa.aiExposure}%</span>
          <svg
            className={`w-5 h-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {isExpanded && (
        <div className="border-t bg-gray-50 p-4 space-y-2">
          {gwa.dwas.map((dwa) => (
            <label
              key={dwa.id}
              className="flex items-center gap-3 p-2 rounded hover:bg-gray-100 cursor-pointer"
            >
              <input
                type="checkbox"
                checked={selectedDwaIds.has(dwa.id)}
                onChange={() => onToggleDwa(dwa.id)}
                className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                aria-label={dwa.title}
              />
              <span className="flex-1 text-sm text-gray-700">{dwa.title}</span>
              <span className="text-xs font-medium text-gray-500">{dwa.aiExposure}% AI exposure</span>
            </label>
          ))}
        </div>
      )}
    </div>
  )
}

export function ActivitiesStep() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const {
    gwaGroups,
    selectedDwaIds,
    isLoading,
    error,
    toggleDwa,
    selectHighExposure,
    selectionCount,
  } = useActivitySelections(sessionId)

  const [expandedGwaIds, setExpandedGwaIds] = useState<Set<string>>(new Set())

  const toggleGwaExpand = (gwaId: string) => {
    setExpandedGwaIds((prev) => {
      const next = new Set(prev)
      if (next.has(gwaId)) {
        next.delete(gwaId)
      } else {
        next.add(gwaId)
      }
      return next
    })
  }

  if (!sessionId) {
    return (
      <div className="flex items-center justify-center p-8">
        <span className="text-red-500" role="alert">
          Error: Session ID is required. Please start a new discovery session.
        </span>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <span className="text-gray-500">Loading activities...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center p-8">
        <span className="text-red-500" role="alert">
          Error: {error}
        </span>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Select Activities</h1>
        <p className="mt-2 text-gray-600">
          Review work activities and select those you want to explore for AI opportunities.
        </p>
      </div>

      <div className="mb-4 flex items-center justify-between">
        <span className="text-sm text-gray-600">{selectionCount} activities selected</span>
        <button
          onClick={() => selectHighExposure()}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Select high exposure
        </button>
      </div>

      <div className="space-y-3">
        {gwaGroups.map((gwa) => (
          <GwaAccordion
            key={gwa.id}
            gwa={gwa}
            isExpanded={expandedGwaIds.has(gwa.id)}
            onToggleExpand={() => toggleGwaExpand(gwa.id)}
            selectedDwaIds={selectedDwaIds}
            onToggleDwa={toggleDwa}
          />
        ))}
      </div>

      {gwaGroups.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No activities found. Please complete the role mapping step first.
        </div>
      )}
    </div>
  )
}
