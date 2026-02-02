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
    <div className="border border-border rounded-lg bg-background overflow-hidden">
      <button
        onClick={onToggleExpand}
        className="w-full flex items-center justify-between p-4 text-left hover:bg-background-muted focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset"
        aria-expanded={isExpanded}
      >
        <div className="flex-1">
          <h3 className="font-medium text-foreground">{gwa.title}</h3>
          <p className="text-sm text-foreground-muted">{gwa.dwas.length} activities</p>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-primary">{gwa.aiExposure}%</span>
          <svg
            className={`w-5 h-5 text-foreground-subtle transition-transform ${isExpanded ? 'rotate-180' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {isExpanded && (
        <div className="border-t border-border bg-background-muted p-4 space-y-2">
          {gwa.dwas.map((dwa) => (
            <label
              key={dwa.id}
              className="flex items-center gap-3 p-2 rounded hover:bg-background-accent cursor-pointer"
            >
              <input
                type="checkbox"
                checked={selectedDwaIds.has(dwa.id)}
                onChange={() => onToggleDwa(dwa.id)}
                className="h-4 w-4 text-primary border-border rounded focus:ring-ring"
                aria-label={dwa.title}
              />
              <span className="flex-1 text-sm text-foreground">{dwa.title}</span>
              <span className="text-xs font-medium text-foreground-muted">{dwa.aiExposure}% AI exposure</span>
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
        <span className="text-destructive" role="alert">
          Error: Session ID is required. Please start a new discovery session.
        </span>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <span className="text-foreground-muted">Loading activities...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center p-8">
        <span className="text-destructive" role="alert">
          Error: {error}
        </span>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-foreground">Select Activities</h1>
        <p className="mt-2 text-foreground-muted">
          Review work activities and select those you want to explore for AI opportunities.
        </p>
      </div>

      <div className="mb-4 flex items-center justify-between">
        <span className="text-sm text-foreground-muted">{selectionCount} activities selected</span>
        <button
          onClick={() => selectHighExposure()}
          className="btn-primary btn-md rounded-lg"
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
        <div className="text-center py-8 text-foreground-muted">
          No activities found. Please complete the role mapping step first.
        </div>
      )}
    </div>
  )
}
