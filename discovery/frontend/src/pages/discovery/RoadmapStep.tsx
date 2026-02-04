import { useState, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import { AppShell } from '../../components/layout/AppShell'
import { DiscoveryWizard, StepContent } from '../../components/layout/DiscoveryWizard'
import { Button } from '../../components/ui/Button'
import { Modal } from '../../components/ui/Modal'
import { TierBadge } from '../../components/ui/Badge'
import { ScorePill } from '../../components/ui/ScoreBar'
import { LoadingState, ErrorState, EmptyState } from '../../components/ui/EmptyState'
import {
  IconRocket,
  IconGripVertical,
  IconArrowRight,
  IconCheckCircle,
} from '../../components/ui/Icons'
import { useRoadmap, RoadmapItem, Phase } from '../../hooks/useRoadmap'

const PHASES: { key: Phase; label: string; description: string; color: string }[] = [
  {
    key: 'NOW',
    label: 'Now',
    description: 'High priority, immediate action',
    color: 'border-success/30 bg-success/5',
  },
  {
    key: 'NEXT',
    label: 'Next',
    description: 'Medium priority, plan for next quarter',
    color: 'border-accent/30 bg-accent/5',
  },
  {
    key: 'LATER',
    label: 'Later',
    description: 'Lower priority, future consideration',
    color: 'border-border bg-bg-muted/30',
  },
]

export function RoadmapStep() {
  const { sessionId } = useParams()

  const {
    items,
    isLoading,
    error,
    updatePhase,
    handoff,
    isHandingOff,
  } = useRoadmap(sessionId || '')

  const [showHandoffModal, setShowHandoffModal] = useState(false)
  const [handoffNotes, setHandoffNotes] = useState('')
  const [draggedItem, setDraggedItem] = useState<RoadmapItem | null>(null)
  const [dragOverPhase, setDragOverPhase] = useState<Phase | null>(null)

  // Group items by phase
  const groupedItems = useMemo(() => {
    const grouped: Record<Phase, RoadmapItem[]> = {
      NOW: [],
      NEXT: [],
      LATER: [],
    }
    items.forEach((item) => {
      grouped[item.phase].push(item)
    })
    // Sort by priority within each phase
    Object.keys(grouped).forEach((phase) => {
      grouped[phase as Phase].sort((a, b) => b.priorityScore - a.priorityScore)
    })
    return grouped
  }, [items])

  // Drag handlers
  const handleDragStart = (item: RoadmapItem) => {
    setDraggedItem(item)
  }

  const handleDragOver = (e: React.DragEvent, phase: Phase) => {
    e.preventDefault()
    setDragOverPhase(phase)
  }

  const handleDragLeave = () => {
    setDragOverPhase(null)
  }

  const handleDrop = async (phase: Phase) => {
    if (draggedItem && draggedItem.phase !== phase) {
      await updatePhase(draggedItem.id, phase)
    }
    setDraggedItem(null)
    setDragOverPhase(null)
  }

  // Handoff handler
  const handleHandoff = async () => {
    const nowItems = groupedItems.NOW.map((item) => item.id)
    if (nowItems.length === 0) return

    await handoff(nowItems, handoffNotes || undefined)
    setShowHandoffModal(false)
    // Could navigate to a success page or show a toast
  }

  const nowCount = groupedItems.NOW.length
  const canHandoff = nowCount > 0

  if (isLoading) {
    return (
      <AppShell>
        <DiscoveryWizard currentStep={5}>
          <LoadingState message="Loading roadmap..." />
        </DiscoveryWizard>
      </AppShell>
    )
  }

  if (error) {
    return (
      <AppShell>
        <DiscoveryWizard currentStep={5}>
          <ErrorState message={error} />
        </DiscoveryWizard>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <DiscoveryWizard currentStep={5} canProceed={false}>
        <StepContent
          title="Implementation Roadmap"
          description="Prioritize and organize your automation candidates into phases."
          actions={
            <Button
              variant="primary"
              size="md"
              icon={<IconRocket size={18} />}
              onClick={() => setShowHandoffModal(true)}
              disabled={!canHandoff}
            >
              Hand off to Build ({nowCount})
            </Button>
          }
        >
          {/* Summary */}
          <div className="grid grid-cols-3 gap-4 mb-8">
            {PHASES.map((phase) => (
              <div key={phase.key} className="surface p-4 text-center">
                <p className="text-2xl font-display font-bold text-default">
                  {groupedItems[phase.key].length}
                </p>
                <p className="text-xs text-muted">
                  {phase.label} Phase
                </p>
              </div>
            ))}
          </div>

          {/* Kanban board */}
          {items.length === 0 ? (
            <EmptyState
              icon={<IconRocket size={28} />}
              title="No candidates yet"
              description="Complete the analysis step to generate automation candidates."
            />
          ) : (
            <div className="grid grid-cols-3 gap-4">
              {PHASES.map((phase) => (
                <div
                  key={phase.key}
                  onDragOver={(e) => handleDragOver(e, phase.key)}
                  onDragLeave={handleDragLeave}
                  onDrop={() => handleDrop(phase.key)}
                  className={`
                    rounded-xl border-2 border-dashed p-3 min-h-[400px]
                    transition-all duration-200
                    ${phase.color}
                    ${dragOverPhase === phase.key ? 'border-accent bg-accent/10 scale-[1.01]' : ''}
                  `}
                >
                  {/* Phase header */}
                  <div className="flex items-center justify-between mb-3 px-1">
                    <div>
                      <h4 className="font-display font-semibold text-default">
                        {phase.label}
                      </h4>
                      <p className="text-xs text-muted">{phase.description}</p>
                    </div>
                    <span className="text-xs font-medium text-muted bg-bg-muted px-2 py-0.5 rounded-full">
                      {groupedItems[phase.key].length}
                    </span>
                  </div>

                  {/* Cards */}
                  <div className="space-y-2">
                    {groupedItems[phase.key].map((item) => (
                      <div
                        key={item.id}
                        draggable
                        onDragStart={() => handleDragStart(item)}
                        className={`
                          surface p-3 cursor-grab active:cursor-grabbing
                          hover:border-accent/30 transition-all
                          ${draggedItem?.id === item.id ? 'opacity-50' : ''}
                        `}
                      >
                        {/* Grip handle */}
                        <div className="flex items-start gap-2">
                          <div className="text-subtle shrink-0 mt-0.5">
                            <IconGripVertical size={14} />
                          </div>

                          <div className="flex-1 min-w-0">
                            {/* Role name */}
                            <p className="font-medium text-sm text-default truncate">
                              {item.roleName}
                            </p>

                            {/* Scores */}
                            <div className="flex items-center gap-2 mt-2">
                              <ScorePill
                                value={item.priorityScore}
                                label="Priority"
                                variant="tier"
                              />
                              <TierBadge tier={item.priorityTier} />
                            </div>

                            {/* Effort */}
                            <div className="mt-2 text-xs text-muted">
                              Effort: <span className="capitalize">{item.estimatedEffort}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}

                    {/* Empty state for column */}
                    {groupedItems[phase.key].length === 0 && (
                      <div className="py-8 text-center text-muted text-sm">
                        Drag items here
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Instructions */}
          <div className="mt-6 p-4 bg-bg-muted rounded-lg">
            <p className="text-sm text-muted">
              <strong className="text-default">Tip:</strong> Drag and drop cards between columns to re-prioritize.
              Items in the "Now" column will be handed off to the Build phase.
            </p>
          </div>
        </StepContent>
      </DiscoveryWizard>

      {/* Handoff modal */}
      <Modal
        isOpen={showHandoffModal}
        onClose={() => setShowHandoffModal(false)}
        title="Hand off to Build"
        description={`You're about to hand off ${nowCount} candidate${nowCount !== 1 ? 's' : ''} to the Build phase.`}
        size="md"
      >
        <div className="space-y-4">
          {/* Candidate list */}
          <div className="max-h-48 overflow-y-auto space-y-2">
            {groupedItems.NOW.map((item) => (
              <div
                key={item.id}
                className="flex items-center gap-3 p-3 bg-bg-muted rounded-lg"
              >
                <IconCheckCircle size={18} className="text-success shrink-0" />
                <span className="text-sm font-medium text-default truncate">
                  {item.roleName}
                </span>
                <TierBadge tier={item.priorityTier} />
              </div>
            ))}
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-default mb-1">
              Notes (optional)
            </label>
            <textarea
              value={handoffNotes}
              onChange={(e) => setHandoffNotes(e.target.value)}
              placeholder="Add any additional context or notes..."
              rows={3}
              className="input resize-none"
            />
          </div>

          {/* Actions */}
          <div className="flex gap-3 justify-end pt-2">
            <Button
              variant="secondary"
              size="md"
              onClick={() => setShowHandoffModal(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="md"
              icon={<IconArrowRight size={18} />}
              onClick={handleHandoff}
              loading={isHandingOff}
            >
              Confirm Handoff
            </Button>
          </div>
        </div>
      </Modal>
    </AppShell>
  )
}
