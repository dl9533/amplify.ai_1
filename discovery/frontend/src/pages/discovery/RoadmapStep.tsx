import { useState, useCallback, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { useRoadmap, Phase, RoadmapCandidate } from '@/hooks/useRoadmap'

// Constants moved outside component to avoid recreating on each render
const PHASES: Phase[] = ['NOW', 'NEXT', 'LATER']

// Generic error message to prevent XSS
const GENERIC_ERROR_MESSAGE = 'An error occurred while loading roadmap data. Please try again.'

interface CandidateCardProps {
  candidate: RoadmapCandidate
  onDragStart: (e: React.DragEvent, candidateId: string) => void
  onMoveToPhase: (candidateId: string, phase: Phase) => void
}

function CandidateCard({ candidate, onDragStart, onMoveToPhase }: CandidateCardProps) {
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'ArrowLeft') {
        e.preventDefault()
        const currentIndex = PHASES.indexOf(candidate.phase)
        if (currentIndex > 0) {
          onMoveToPhase(candidate.id, PHASES[currentIndex - 1])
        }
      } else if (e.key === 'ArrowRight') {
        e.preventDefault()
        const currentIndex = PHASES.indexOf(candidate.phase)
        if (currentIndex < PHASES.length - 1) {
          onMoveToPhase(candidate.id, PHASES[currentIndex + 1])
        }
      }
    },
    [candidate.id, candidate.phase, onMoveToPhase]
  )

  // Get available phases to move to (exclude current phase)
  const availablePhases = PHASES.filter((phase) => phase !== candidate.phase)

  return (
    <div
      tabIndex={0}
      draggable="true"
      onDragStart={(e) => onDragStart(e, candidate.id)}
      onKeyDown={handleKeyDown}
      className="card p-4 cursor-grab hover:shadow-md transition-shadow focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      aria-label={`${candidate.name} card in ${candidate.phase} phase. Use arrow keys to move between phases.`}
    >
      <h4 className="text-base font-medium text-foreground mb-2">{candidate.name}</h4>
      <div className="text-sm text-foreground-muted space-y-1">
        <div>Priority: {candidate.priorityScore.toFixed(2)}</div>
        <div>Exposure: {candidate.exposureScore.toFixed(2)}</div>
      </div>
      {/* Keyboard-accessible move buttons */}
      <div className="mt-3 flex gap-2 flex-wrap">
        {availablePhases.map((phase) => (
          <button
            key={phase}
            type="button"
            onClick={() => onMoveToPhase(candidate.id, phase)}
            className="px-2 py-1 text-xs font-medium text-primary bg-primary/10 rounded hover:bg-primary/20 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            aria-label={`Move ${candidate.name} to ${phase}`}
          >
            Move to {phase}
          </button>
        ))}
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
  onMoveToPhase: (candidateId: string, phase: Phase) => void
}

function KanbanColumn({ phase, candidates, onDragStart, onDragOver, onDrop, onMoveToPhase }: KanbanColumnProps) {
  const phaseColors: Record<Phase, string> = {
    NOW: 'border-success bg-success/10',
    NEXT: 'border-primary bg-primary/10',
    LATER: 'border-border bg-background-muted',
  }

  return (
    <div
      className={`flex-1 min-w-[280px] border-t-4 ${phaseColors[phase]} rounded-lg p-4`}
      onDragOver={onDragOver}
      onDrop={(e) => onDrop(e, phase)}
      aria-label={`${phase} column`}
    >
      <h3 className="text-lg font-bold text-foreground mb-4">{phase}</h3>
      <div className="space-y-3">
        {candidates.map((candidate) => (
          <CandidateCard
            key={candidate.id}
            candidate={candidate}
            onDragStart={onDragStart}
            onMoveToPhase={onMoveToPhase}
          />
        ))}
        {candidates.length === 0 && (
          <div className="text-center py-8 text-foreground-subtle italic">
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
  const cancelButtonRef = useRef<HTMLButtonElement>(null)
  const confirmButtonRef = useRef<HTMLButtonElement>(null)
  const modalRef = useRef<HTMLDivElement>(null)

  // Focus cancel button when modal opens
  useEffect(() => {
    if (isOpen && cancelButtonRef.current) {
      cancelButtonRef.current.focus()
    }
  }, [isOpen])

  // Handle Escape key and focus trap
  useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isHandingOff) {
        onCancel()
        return
      }

      // Focus trap: trap Tab navigation between Cancel and Confirm buttons
      if (e.key === 'Tab') {
        const focusableElements = [cancelButtonRef.current, confirmButtonRef.current].filter(
          (el): el is HTMLButtonElement => el !== null && !el.disabled
        )

        if (focusableElements.length === 0) return

        const firstElement = focusableElements[0]
        const lastElement = focusableElements[focusableElements.length - 1]

        if (e.shiftKey) {
          // Shift+Tab: if on first element, go to last
          if (document.activeElement === firstElement) {
            e.preventDefault()
            lastElement.focus()
          }
        } else {
          // Tab: if on last element, go to first
          if (document.activeElement === lastElement) {
            e.preventDefault()
            firstElement.focus()
          }
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, isHandingOff, onCancel])

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="handoff-modal-title"
      ref={modalRef}
    >
      <div className="card p-6 max-w-md w-full mx-4 shadow-xl">
        <h2 id="handoff-modal-title" className="text-xl font-bold text-foreground mb-4">
          Confirm Handoff
        </h2>
        <p className="text-foreground-muted mb-6">
          Are you sure you want to send these candidates to the intake process? This action will
          initiate the AI agent creation workflow for all prioritized roles.
        </p>
        <div className="flex justify-end gap-3">
          <button
            ref={cancelButtonRef}
            type="button"
            onClick={onCancel}
            disabled={isHandingOff}
            className="btn-secondary btn-md rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Cancel handoff"
          >
            Cancel
          </button>
          <button
            ref={confirmButtonRef}
            type="button"
            onClick={onConfirm}
            disabled={isHandingOff}
            className="btn-primary btn-md rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
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
    handoffError,
  } = useRoadmap(sessionId)

  const [draggedCandidateId, setDraggedCandidateId] = useState<string | null>(null)
  const [isHandoffModalOpen, setIsHandoffModalOpen] = useState(false)
  const [phaseAnnouncement, setPhaseAnnouncement] = useState<string>('')

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
        const candidate = candidates.find((c) => c.id === draggedCandidateId)
        if (candidate && candidate.phase !== phase) {
          updatePhase(draggedCandidateId, phase)
          setPhaseAnnouncement(`${candidate.name} moved to ${phase} phase`)
        }
        setDraggedCandidateId(null)
      }
    },
    [draggedCandidateId, updatePhase, candidates]
  )

  const handleMoveToPhase = useCallback(
    (candidateId: string, phase: Phase) => {
      const candidate = candidates.find((c) => c.id === candidateId)
      if (candidate && candidate.phase !== phase) {
        updatePhase(candidateId, phase)
        setPhaseAnnouncement(`${candidate.name} moved to ${phase} phase`)
      }
    },
    [candidates, updatePhase]
  )

  const handleExport = useCallback(() => {
    const exportData = JSON.stringify(candidates, null, 2)
    const blob = new Blob([exportData], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    try {
      link.href = url
      link.download = `roadmap-${sessionId || 'export'}.json`
      document.body.appendChild(link)
      link.click()
    } finally {
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    }
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
      // Close modal on error so user isn't stuck
      setIsHandoffModalOpen(false)
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
        <span className="text-destructive" role="alert">
          Error: Session ID is required. Please start a new discovery session.
        </span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center p-8">
        <span className="text-destructive" role="alert">
          {GENERIC_ERROR_MESSAGE}
        </span>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* ARIA live region for phase update announcements */}
      <div aria-live="polite" aria-atomic="true" className="sr-only">
        {phaseAnnouncement}
      </div>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-foreground">Implementation Roadmap</h1>
        <p className="mt-2 text-foreground-muted">
          Organize AI candidates into implementation phases. Drag cards between columns to adjust priorities.
        </p>
      </div>

      {/* Handoff Error Display */}
      {handoffError && (
        <div className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-md" role="alert">
          <span className="text-destructive">{handoffError}</span>
        </div>
      )}

      {/* Action Buttons */}
      <div className="mb-6 flex justify-end gap-3">
        <button
          type="button"
          onClick={handleExport}
          className="btn-secondary btn-md rounded-md"
          aria-label="Export roadmap"
        >
          Export
        </button>
        <button
          type="button"
          onClick={handleSendToIntake}
          className="btn-primary btn-md rounded-md"
          aria-label="Send to Intake"
        >
          Send to Intake
        </button>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center p-8" role="status" aria-live="polite">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <span className="ml-3 text-foreground-muted">Loading roadmap...</span>
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
              onMoveToPhase={handleMoveToPhase}
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
