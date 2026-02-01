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

export function KanbanTimeline({
  items,
  onPhaseChange,
}: KanbanTimelineProps): React.ReactElement {
  const [draggedItemId, setDraggedItemId] = useState<string | null>(null)
  const [dragOverPhase, setDragOverPhase] = useState<Phase | null>(null)

  const itemsByPhase = useMemo(() => {
    const grouped: Record<Phase, KanbanItem[]> = {
      NOW: [],
      NEXT: [],
      LATER: [],
    }

    items.forEach((item) => {
      if (grouped[item.phase as Phase]) {
        grouped[item.phase as Phase].push(item)
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
    },
    []
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
        onPhaseChange(draggedItemId, phase)
        setDraggedItemId(null)
      }
    },
    [draggedItemId, onPhaseChange]
  )

  return (
    <div
      className="grid grid-cols-3 gap-4 h-full"
      role="region"
      aria-label="Kanban timeline board"
    >
      {PHASES.map((phase) => {
        const columnItems = itemsByPhase[phase]
        const isDropTarget = dragOverPhase === phase
        const count = columnItems.length

        return (
          <div
            key={phase}
            data-testid={`column-${phase}`}
            className={`flex flex-col bg-gray-50 rounded-lg border transition-all ${
              isDropTarget
                ? 'ring-2 ring-blue-500 border-blue-300 bg-blue-50'
                : 'border-gray-200'
            }`}
            onDragOver={handleDragOver}
            onDragEnter={(e) => handleDragEnter(e, phase)}
            onDragLeave={handleDragLeave}
            onDrop={(e) => handleDrop(e, phase)}
            role="group"
            aria-label={`${PHASE_LABELS[phase]} phase column with ${count} items`}
          >
            {/* Column Header */}
            <div className="p-3 border-b border-gray-200">
              <h3 className="font-semibold text-gray-900">
                {phase} ({count})
              </h3>
              <p className="text-xs text-gray-500 mt-1">
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
                  />
                ))
              ) : (
                <div
                  className="flex items-center justify-center h-full text-gray-400 text-sm italic"
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
