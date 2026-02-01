import React, { useCallback, memo } from 'react'

export interface KanbanItem {
  id: string
  name: string
  phase: 'NOW' | 'NEXT' | 'LATER'
  priorityScore: number
}

export interface KanbanCardProps {
  item: KanbanItem
  onDragStart: (e: React.DragEvent, itemId: string) => void
  onKeyboardMove?: (itemId: string, direction: 'left' | 'right') => void
  isGrabbed?: boolean
}

/** Utility function to get priority color classes based on score */
export function getPriorityColor(score: number): string {
  if (score >= 0.8) return 'bg-green-100 text-green-800'
  if (score >= 0.6) return 'bg-yellow-100 text-yellow-800'
  return 'bg-gray-100 text-gray-800'
}

export const KanbanCard = memo(function KanbanCard({
  item,
  onDragStart,
  onKeyboardMove,
  isGrabbed = false,
}: KanbanCardProps): React.ReactElement {
  const handleDragStart = useCallback(
    (e: React.DragEvent) => {
      onDragStart(e, item.id)
    },
    [onDragStart, item.id]
  )

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (!onKeyboardMove) return

      if (e.key === 'ArrowLeft') {
        e.preventDefault()
        onKeyboardMove(item.id, 'left')
      } else if (e.key === 'ArrowRight') {
        e.preventDefault()
        onKeyboardMove(item.id, 'right')
      }
    },
    [onKeyboardMove, item.id]
  )

  return (
    <div
      draggable="true"
      onDragStart={handleDragStart}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      className="bg-white border border-gray-200 rounded-lg p-3 shadow-sm cursor-grab active:cursor-grabbing hover:shadow-md transition-shadow focus:outline-none focus:ring-2 focus:ring-blue-500"
      role="listitem"
      aria-label={`${item.name} with priority score ${(item.priorityScore * 100).toFixed(0)}%. Use arrow keys to move between phases.`}
      aria-grabbed={isGrabbed}
    >
      <div className="font-medium text-gray-900 mb-2">{item.name}</div>
      <div className="flex items-center justify-between">
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getPriorityColor(item.priorityScore)}`}
        >
          {(item.priorityScore * 100).toFixed(0)}% priority
        </span>
      </div>
    </div>
  )
})
