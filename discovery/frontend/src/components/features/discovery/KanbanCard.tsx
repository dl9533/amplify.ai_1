import React from 'react'

export interface KanbanItem {
  id: string
  name: string
  phase: 'NOW' | 'NEXT' | 'LATER'
  priorityScore: number
}

export interface KanbanCardProps {
  item: KanbanItem
  onDragStart: (e: React.DragEvent, itemId: string) => void
}

export function KanbanCard({ item, onDragStart }: KanbanCardProps): React.ReactElement {
  const handleDragStart = (e: React.DragEvent) => {
    onDragStart(e, item.id)
  }

  const getPriorityColor = (score: number): string => {
    if (score >= 0.8) return 'bg-green-100 text-green-800'
    if (score >= 0.6) return 'bg-yellow-100 text-yellow-800'
    return 'bg-gray-100 text-gray-800'
  }

  return (
    <div
      draggable="true"
      onDragStart={handleDragStart}
      className="bg-white border border-gray-200 rounded-lg p-3 shadow-sm cursor-grab active:cursor-grabbing hover:shadow-md transition-shadow"
      role="listitem"
      aria-label={`${item.name} with priority score ${(item.priorityScore * 100).toFixed(0)}%`}
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
}
