import { useState, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { useRoadmap, Phase, RoadmapCandidate } from '@/hooks/useRoadmap'

// Constants moved outside component to avoid recreating on each render
const PHASES: Phase[] = ['NOW', 'NEXT', 'LATER']

// Generic error message to prevent XSS
const GENERIC_ERROR_MESSAGE = 'An error occurred while loading roadmap data. Please try again.'

interface CandidateCardProps {
  candidate: RoadmapCandidate
  onDragStart: (e: React.DragEvent, candidateId: string) => void
}

function CandidateCard({ candidate, onDragStart }: CandidateCardProps) {
  return (
    <div
      draggable="true"
      onDragStart={(e) => onDragStart(e, candidate.id)}
      className="bg-white border rounded-lg p-4 shadow-sm cursor-grab hover:shadow-md transition-shadow"
      aria-label={`${candidate.name} card`}
    >
      <h4 className="text-base font-medium text-gray-900 mb-2">{candidate.name}</h4>
      <div className="text-sm text-gray-600 space-y-1">
        <div>Priority: {candidate.priorityScore.toFixed(2)}</div>
        <div>Exposure: {candidate.exposureScore.toFixed(2)}</div>
      </div>
    </div>
  )
}

interface KanbanColumnProps {
  phase: Phase
  candidates: RoadmapCandidate[]
  onDragStart: (e: React.DragEvent, candidateId: string) => void
  onDragOver: (e: React.DragEvent) => void
  onDrop: (e: React.DragEvent, phase: Phase) => void
}

function KanbanColumn({ phase, candidates, onDragStart, onDragOver, onDrop }: KanbanColumnProps) {
  const phaseColors: Record<Phase, string> = {
    NOW: 'border-green-500 bg-green-50',
    NEXT: 'border-blue-500 bg-blue-50',
    LATER: 'border-gray-500 bg-gray-50',
  }

  return (
    <div
      className={`flex-1 min-w-[280px] border-t-4 ${phaseColors[phase]} rounded-lg p-4`}
      onDragOver={onDragOver}
      onDrop={(e) => onDrop(e, phase)}
      aria-label={`${phase} column`}
    >
      <h3 className="text-lg font-bold text-gray-900 mb-4">{phase}</h3>
      <div className="space-y-3">
        {candidates.map((candidate) => (
          <CandidateCard
            key={candidate.id}
            candidate={candidate}
            onDragStart={onDragStart}
          />
        ))}
        {candidates.length === 0 && (
          <div className="text-center py-8 text-gray-400 italic">
            No candidates in this phase
          </div>
        )}
      </div>
    </div>
  )
}

interface HandoffModalProps {
  isOpen: boolean
  onConfirm: () => void
  onCancel: () => void
  isHandingOff: boolean
}

function HandoffModal({ isOpen, onConfirm, onCancel, isHandingOff }: HandoffModalProps) {
  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="handoff-modal-title"
    >
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
        <h2 id="handoff-modal-title" className="text-xl font-bold text-gray-900 mb-4">
          Confirm Handoff
        </h2>
        <p className="text-gray-600 mb-6">
          Are you sure you want to send these candidates to the intake process? This action will
          initiate the AI agent creation workflow for all prioritized roles.
        </p>
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            disabled={isHandingOff}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 disabled:opacity-50"
            aria-label="Cancel handoff"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isHandingOff}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
            aria-label="Confirm handoff"
          >
            {isHandingOff ? 'Sending...' : 'Confirm'}
          </button>
        </div>
      </div>
    </div>
  )
}

export function RoadmapStep() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const {
    candidates,
    isLoading,
    error,
    updatePhase,
    handoff,
    isHandingOff,
  } = useRoadmap(sessionId)

  const [draggedCandidateId, setDraggedCandidateId] = useState<string | null>(null)
  const [isHandoffModalOpen, setIsHandoffModalOpen] = useState(false)

  const handleDragStart = useCallback((e: React.DragEvent, candidateId: string) => {
    setDraggedCandidateId(candidateId)
    e.dataTransfer.effectAllowed = 'move'
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent, phase: Phase) => {
      e.preventDefault()
      if (draggedCandidateId) {
        updatePhase(draggedCandidateId, phase)
        setDraggedCandidateId(null)
      }
    },
    [draggedCandidateId, updatePhase]
  )

  const handleExport = useCallback(() => {
    // TODO: Implement export functionality (CSV, JSON, etc.)
    const exportData = JSON.stringify(candidates, null, 2)
    const blob = new Blob([exportData], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `roadmap-${sessionId || 'export'}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }, [candidates, sessionId])

  const handleSendToIntake = useCallback(() => {
    setIsHandoffModalOpen(true)
  }, [])

  const handleConfirmHandoff = useCallback(async () => {
    try {
      await handoff()
      setIsHandoffModalOpen(false)
      // TODO: Navigate to success page or show success message
    } catch {
      // Error is handled by the hook
    }
  }, [handoff])

  const handleCancelHandoff = useCallback(() => {
    setIsHandoffModalOpen(false)
  }, [])

  // Group candidates by phase
  const candidatesByPhase = PHASES.reduce(
    (acc, phase) => {
      acc[phase] = candidates.filter((c) => c.phase === phase)
      return acc
    },
    {} as Record<Phase, RoadmapCandidate[]>
  )

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
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Implementation Roadmap</h1>
        <p className="mt-2 text-gray-600">
          Organize AI candidates into implementation phases. Drag cards between columns to adjust priorities.
        </p>
      </div>

      {/* Action Buttons */}
      <div className="mb-6 flex justify-end gap-3">
        <button
          type="button"
          onClick={handleExport}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          aria-label="Export roadmap"
        >
          Export
        </button>
        <button
          type="button"
          onClick={handleSendToIntake}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
          aria-label="Send to Intake"
        >
          Send to Intake
        </button>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center p-8" role="status" aria-live="polite">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-500">Loading roadmap...</span>
        </div>
      )}

      {/* Kanban Board */}
      {!isLoading && (
        <div className="flex gap-6 overflow-x-auto pb-4" role="region" aria-label="Roadmap kanban board">
          {PHASES.map((phase) => (
            <KanbanColumn
              key={phase}
              phase={phase}
              candidates={candidatesByPhase[phase]}
              onDragStart={handleDragStart}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
            />
          ))}
        </div>
      )}

      {/* Handoff Confirmation Modal */}
      <HandoffModal
        isOpen={isHandoffModalOpen}
        onConfirm={handleConfirmHandoff}
        onCancel={handleCancelHandoff}
        isHandingOff={isHandingOff}
      />
    </div>
  )
}
