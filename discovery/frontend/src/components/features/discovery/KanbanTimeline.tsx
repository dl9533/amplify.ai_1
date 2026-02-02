import React, { useMemo, useState, useCallback } from 'react'
import { KanbanCard, KanbanItem } from './KanbanCard'

export type Phase = 'NOW' | 'NEXT' | 'LATER'

export interface KanbanTimelineProps {
  items: KanbanItem[]
  onPhaseChange: (itemId: string, newPhase: Phase) => void
}

const PHASES: Phase[] = ['NOW', 'NEXT', 'LATER']

const PHASE_LABELS: Record<Phase, string> = {
  NOW: 'Now',
  NEXT: 'Next',
  LATER: 'Later',
}

const PHASE_DESCRIPTIONS: Record<Phase, string> = {
  NOW: 'High priority - immediate action',
  NEXT: 'Medium priority - coming soon',
  LATER: 'Lower priority - future planning',
}

/** Validates if a string is a valid Phase */
function isValidPhase(phase: string): phase is Phase {
  return PHASES.includes(phase as Phase)
}

export function KanbanTimeline({
  items,
  onPhaseChange,
}: KanbanTimelineProps): React.ReactElement {
  const [draggedItemId, setDraggedItemId] = useState<string | null>(null)
  const [dragOverPhase, setDragOverPhase] = useState<Phase | null>(null)
  const [announcement, setAnnouncement] = useState<string>('')

  const itemsByPhase = useMemo(() => {
    const grouped: Record<Phase, KanbanItem[]> = {
      NOW: [],
      NEXT: [],
      LATER: [],
    }

    items.forEach((item) => {
      if (isValidPhase(item.phase)) {
        grouped[item.phase].push(item)
      } else {
        console.warn(
          `KanbanTimeline: Invalid phase "${item.phase}" for item "${item.id}". ` +
            `Expected one of: ${PHASES.join(', ')}`
        )
      }
    })

    return grouped
  }, [items])

  const handleDragStart = useCallback(
    (e: React.DragEvent, itemId: string) => {
      setDraggedItemId(itemId)
      if (e.dataTransfer) {
        e.dataTransfer.effectAllowed = 'move'
        e.dataTransfer.setData('text/plain', itemId)
      }
      const item = items.find((i) => i.id === itemId)
      if (item) {
        setAnnouncement(`Started dragging ${item.name}`)
      }
    },
    [items]
  )

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    if (e.dataTransfer) {
      e.dataTransfer.dropEffect = 'move'
    }
  }, [])

  const handleDragEnter = useCallback((e: React.DragEvent, phase: Phase) => {
    e.preventDefault()
    setDragOverPhase(phase)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    // Only clear if we're leaving the column itself, not a child element
    const relatedTarget = e.relatedTarget as HTMLElement
    const currentTarget = e.currentTarget as HTMLElement
    if (!currentTarget.contains(relatedTarget)) {
      setDragOverPhase(null)
    }
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent, phase: Phase) => {
      e.preventDefault()
      setDragOverPhase(null)

      if (draggedItemId) {
        const item = items.find((i) => i.id === draggedItemId)
        onPhaseChange(draggedItemId, phase)
        setDraggedItemId(null)
        if (item) {
          setAnnouncement(`Moved ${item.name} to ${PHASE_LABELS[phase]} phase`)
        }
      }
    },
    [draggedItemId, onPhaseChange, items]
  )

  const handleKeyboardMove = useCallback(
    (itemId: string, direction: 'left' | 'right') => {
      const item = items.find((i) => i.id === itemId)
      if (!item) return

      const currentPhaseIndex = PHASES.indexOf(item.phase)
      let newPhaseIndex: number

      if (direction === 'left') {
        newPhaseIndex = Math.max(0, currentPhaseIndex - 1)
      } else {
        newPhaseIndex = Math.min(PHASES.length - 1, currentPhaseIndex + 1)
      }

      if (newPhaseIndex !== currentPhaseIndex) {
        const newPhase = PHASES[newPhaseIndex]
        onPhaseChange(itemId, newPhase)
        setAnnouncement(`Moved ${item.name} to ${PHASE_LABELS[newPhase]} phase`)
      }
    },
    [items, onPhaseChange]
  )

  return (
    <div
      className="grid grid-cols-3 gap-4 h-full"
      role="region"
      aria-label="Kanban timeline board"
    >
      {/* Live region for announcements */}
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      >
        {announcement}
      </div>

      {PHASES.map((phase) => {
        const columnItems = itemsByPhase[phase]
        const isDropTarget = dragOverPhase === phase
        const count = columnItems.length

        return (
          <div
            key={phase}
            data-testid={`column-${phase}`}
            className={`flex flex-col bg-background-muted rounded-lg border transition-all ${
              isDropTarget
                ? 'ring-2 ring-primary border-primary bg-primary/10'
                : 'border-border'
            }`}
            onDragOver={handleDragOver}
            onDragEnter={(e) => handleDragEnter(e, phase)}
            onDragLeave={handleDragLeave}
            onDrop={(e) => handleDrop(e, phase)}
            role="group"
            aria-label={`${PHASE_LABELS[phase]} phase column with ${count} items`}
            aria-dropeffect={draggedItemId ? 'move' : 'none'}
          >
            {/* Column Header */}
            <div className="p-3 border-b border-border">
              <h3 className="font-semibold text-foreground">
                {phase} ({count})
              </h3>
              <p className="text-xs text-foreground-muted mt-1">
                {PHASE_DESCRIPTIONS[phase]}
              </p>
            </div>

            {/* Column Content */}
            <div
              className="flex-1 p-3 space-y-2 overflow-y-auto min-h-[200px]"
              role="list"
              aria-label={`Items in ${PHASE_LABELS[phase]} phase`}
            >
              {columnItems.length > 0 ? (
                columnItems.map((item) => (
                  <KanbanCard
                    key={item.id}
                    item={item}
                    onDragStart={handleDragStart}
                    onKeyboardMove={handleKeyboardMove}
                    isGrabbed={draggedItemId === item.id}
                  />
                ))
              ) : (
                <div
                  className="flex items-center justify-center h-full text-foreground-subtle text-sm italic"
                  role="status"
                  aria-label="Empty column"
                >
                  Drag items here
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
