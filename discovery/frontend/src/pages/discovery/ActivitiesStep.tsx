import { useState, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import { AppShell } from '../../components/layout/AppShell'
import { DiscoveryWizard, StepContent } from '../../components/layout/DiscoveryWizard'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { ScoreBar, ScorePill } from '../../components/ui/ScoreBar'
import { LoadingState, ErrorState } from '../../components/ui/EmptyState'
import {
  IconChevronDown,
  IconChevronUp,
  IconZap,
  IconCheck,
} from '../../components/ui/Icons'
import { useActivitySelections, GWA, DWA } from '../../hooks/useActivitySelections'

export function ActivitiesStep() {
  const { sessionId } = useParams()
  const {
    activities,
    selectedIds,
    isLoading,
    error,
    toggleDwa,
    bulkSelectByExposure,
  } = useActivitySelections(sessionId || '')

  const [expandedGwas, setExpandedGwas] = useState<Set<string>>(new Set())

  // Calculate stats
  const stats = useMemo(() => {
    let totalDwas = 0
    let selectedDwas = selectedIds.size
    let avgExposure = 0

    activities.forEach((gwa) => {
      totalDwas += gwa.dwas.length
      const selectedInGwa = gwa.dwas.filter((d) => selectedIds.has(d.id))
      selectedInGwa.forEach((d) => {
        avgExposure += d.aiExposure
      })
    })

    avgExposure = selectedDwas > 0 ? avgExposure / selectedDwas : 0

    return { totalDwas, selectedDwas, avgExposure }
  }, [activities, selectedIds])

  const toggleGwa = (gwaId: string) => {
    setExpandedGwas((prev) => {
      const next = new Set(prev)
      if (next.has(gwaId)) {
        next.delete(gwaId)
      } else {
        next.add(gwaId)
      }
      return next
    })
  }

  const handleBulkSelect = async () => {
    await bulkSelectByExposure(0.7) // Select DWAs with >70% AI exposure
  }

  const canProceed = stats.selectedDwas > 0

  if (isLoading) {
    return (
      <AppShell>
        <DiscoveryWizard currentStep={3}>
          <LoadingState message="Loading activities..." />
        </DiscoveryWizard>
      </AppShell>
    )
  }

  if (error) {
    return (
      <AppShell>
        <DiscoveryWizard currentStep={3}>
          <ErrorState message={error} />
        </DiscoveryWizard>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <DiscoveryWizard currentStep={3} canProceed={canProceed}>
        <StepContent
          title="Select Work Activities"
          description="Choose the detailed work activities (DWAs) that apply to each role. Activities with high AI exposure are pre-selected."
          actions={
            <Button
              variant="secondary"
              size="sm"
              icon={<IconZap size={16} />}
              onClick={handleBulkSelect}
            >
              Auto-select high exposure
            </Button>
          }
        >
          {/* Summary stats */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="surface p-4 text-center">
              <p className="text-2xl font-display font-bold text-default">
                {stats.selectedDwas}
              </p>
              <p className="text-xs text-muted">Activities Selected</p>
            </div>
            <div className="surface p-4 text-center">
              <p className="text-2xl font-display font-bold text-default">
                {stats.totalDwas}
              </p>
              <p className="text-xs text-muted">Total Activities</p>
            </div>
            <div className="surface p-4 text-center">
              <p className="text-2xl font-display font-bold text-accent">
                {Math.round(stats.avgExposure * 100)}%
              </p>
              <p className="text-xs text-muted">Avg AI Exposure</p>
            </div>
          </div>

          {/* GWA accordion list */}
          <div className="space-y-3">
            {activities.map((gwa, gwaIndex) => {
              const isExpanded = expandedGwas.has(gwa.id)
              const selectedInGwa = gwa.dwas.filter((d) => selectedIds.has(d.id)).length
              const totalInGwa = gwa.dwas.length

              return (
                <div
                  key={gwa.id}
                  className="surface overflow-hidden animate-slide-up"
                  style={{ animationDelay: `${Math.min(gwaIndex, 8) * 50}ms` }}
                >
                  {/* GWA header */}
                  <button
                    onClick={() => toggleGwa(gwa.id)}
                    className="w-full p-4 flex items-center gap-4 text-left hover:bg-bg-muted/50 transition-colors"
                  >
                    {/* Expand icon */}
                    <div className="shrink-0 text-muted">
                      {isExpanded ? (
                        <IconChevronUp size={20} />
                      ) : (
                        <IconChevronDown size={20} />
                      )}
                    </div>

                    {/* GWA info */}
                    <div className="flex-1 min-w-0">
                      <h4 className="font-display font-medium text-default truncate">
                        {gwa.title}
                      </h4>
                      <div className="flex items-center gap-3 mt-1">
                        <span className="text-xs text-muted">
                          {selectedInGwa}/{totalInGwa} selected
                        </span>
                        {gwa.aiExposure && (
                          <ScorePill
                            value={gwa.aiExposure}
                            label="AI Exposure"
                            variant="tier"
                          />
                        )}
                      </div>
                    </div>

                    {/* Selection progress ring */}
                    <div className="shrink-0 w-10 h-10 relative">
                      <svg className="w-10 h-10 -rotate-90">
                        <circle
                          cx="20"
                          cy="20"
                          r="16"
                          fill="none"
                          strokeWidth="3"
                          className="stroke-bg-muted"
                        />
                        <circle
                          cx="20"
                          cy="20"
                          r="16"
                          fill="none"
                          strokeWidth="3"
                          strokeDasharray={`${(selectedInGwa / totalInGwa) * 100.53} 100.53`}
                          className="stroke-accent transition-all duration-300"
                        />
                      </svg>
                      <span className="absolute inset-0 flex items-center justify-center text-xs font-medium text-muted">
                        {selectedInGwa}
                      </span>
                    </div>
                  </button>

                  {/* DWA list (expanded) */}
                  {isExpanded && (
                    <div className="border-t border-border">
                      {gwa.dwas.map((dwa) => {
                        const isSelected = selectedIds.has(dwa.id)

                        return (
                          <label
                            key={dwa.id}
                            className={`
                              flex items-start gap-3 p-4 cursor-pointer
                              border-b border-border last:border-0
                              hover:bg-bg-muted/50 transition-colors
                              ${isSelected ? 'bg-accent/5' : ''}
                            `}
                          >
                            {/* Checkbox */}
                            <div className="relative shrink-0 mt-0.5">
                              <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={() => toggleDwa(dwa.id)}
                                className="sr-only peer"
                              />
                              <div
                                className={`
                                  w-5 h-5 rounded border-2 flex items-center justify-center
                                  transition-all duration-150
                                  ${
                                    isSelected
                                      ? 'bg-accent border-accent'
                                      : 'border-border bg-bg-muted'
                                  }
                                `}
                              >
                                {isSelected && (
                                  <IconCheck size={12} className="text-white" />
                                )}
                              </div>
                            </div>

                            {/* DWA content */}
                            <div className="flex-1 min-w-0">
                              <p
                                className={`
                                  text-sm
                                  ${isSelected ? 'text-default font-medium' : 'text-muted'}
                                `}
                              >
                                {dwa.title}
                              </p>
                              {dwa.description && (
                                <p className="text-xs text-subtle mt-1 line-clamp-2">
                                  {dwa.description}
                                </p>
                              )}
                            </div>

                            {/* AI exposure score */}
                            <div className="shrink-0 w-20">
                              <ScoreBar
                                value={dwa.aiExposure}
                                size="sm"
                                variant="tier"
                              />
                            </div>
                          </label>
                        )
                      })}
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {/* Empty state */}
          {activities.length === 0 && (
            <div className="text-center py-12">
              <p className="text-muted">
                No activities found. Please complete role mapping first.
              </p>
            </div>
          )}
        </StepContent>
      </DiscoveryWizard>
    </AppShell>
  )
}
