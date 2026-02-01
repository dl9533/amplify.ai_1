import { useState, useCallback, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { useDiscoverySessions, DiscoverySession } from '@/hooks/useDiscoverySessions'

const GENERIC_ERROR_MESSAGE = 'An error occurred while loading sessions. Please try again.'

interface DeleteConfirmModalProps {
  isOpen: boolean
  sessionName: string
  onConfirm: () => void
  onCancel: () => void
  isDeleting: boolean
}

function DeleteConfirmModal({ isOpen, sessionName, onConfirm, onCancel, isDeleting }: DeleteConfirmModalProps) {
  const cancelButtonRef = useRef<HTMLButtonElement>(null)
  const confirmButtonRef = useRef<HTMLButtonElement>(null)

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
      if (e.key === 'Escape' && !isDeleting) {
        onCancel()
        return
      }

      // Focus trap
      if (e.key === 'Tab') {
        const focusableElements = [cancelButtonRef.current, confirmButtonRef.current].filter(
          (el): el is HTMLButtonElement => el !== null && !el.disabled
        )

        if (focusableElements.length === 0) return

        const firstElement = focusableElements[0]
        const lastElement = focusableElements[focusableElements.length - 1]

        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault()
            lastElement.focus()
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault()
            firstElement.focus()
          }
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, isDeleting, onCancel])

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="delete-modal-title"
    >
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
        <h2 id="delete-modal-title" className="text-xl font-bold text-gray-900 mb-4">
          Confirm Delete
        </h2>
        <p className="text-gray-600 mb-6">
          Are you sure you want to delete the session "{sessionName}"? This action cannot be undone.
        </p>
        <div className="flex justify-end gap-3">
          <button
            ref={cancelButtonRef}
            type="button"
            onClick={onCancel}
            disabled={isDeleting}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Cancel delete"
          >
            Cancel
          </button>
          <button
            ref={confirmButtonRef}
            type="button"
            onClick={onConfirm}
            disabled={isDeleting}
            className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Confirm delete"
          >
            {isDeleting ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  )
}

interface SessionCardProps {
  session: DiscoverySession
  onDelete: (session: DiscoverySession) => void
  isDeleting: boolean
}

function SessionCard({ session, onDelete, isDeleting }: SessionCardProps) {
  const statusColors: Record<string, string> = {
    Draft: 'bg-gray-100 text-gray-700',
    'In Progress': 'bg-blue-100 text-blue-700',
    Completed: 'bg-green-100 text-green-700',
    Archived: 'bg-yellow-100 text-yellow-700',
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  return (
    <div className="bg-white border rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-lg font-medium text-gray-900">{session.name}</h3>
          <div className="mt-2 flex items-center gap-3">
            <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${statusColors[session.status]}`}>
              {session.status}
            </span>
            <span className="text-sm text-gray-500">
              Step {session.currentStep} of {session.totalSteps}
            </span>
          </div>
          <p className="mt-2 text-sm text-gray-500">
            Created {formatDate(session.createdAt)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            to={`/discovery/${session.id}`}
            className="px-3 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-md hover:bg-blue-100"
            aria-label={`Continue ${session.name}`}
          >
            Continue
          </Link>
          <button
            type="button"
            onClick={() => onDelete(session)}
            disabled={isDeleting}
            className="px-3 py-2 text-sm font-medium text-red-600 bg-red-50 rounded-md hover:bg-red-100 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label={`Delete ${session.name}`}
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  )
}

interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}

function Pagination({ currentPage, totalPages, onPageChange }: PaginationProps) {
  const pages = Array.from({ length: totalPages }, (_, i) => i + 1)

  return (
    <nav role="navigation" aria-label="Pagination" className="flex items-center justify-center gap-2 mt-6">
      <button
        type="button"
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        aria-label="Previous page"
      >
        Previous
      </button>
      <div className="flex items-center gap-1">
        {pages.map((page) => (
          <button
            key={page}
            type="button"
            onClick={() => onPageChange(page)}
            className={`px-3 py-2 text-sm font-medium rounded-md ${
              page === currentPage
                ? 'bg-blue-600 text-white'
                : 'text-gray-700 bg-white border hover:bg-gray-50'
            }`}
            aria-label={`Page ${page}`}
            aria-current={page === currentPage ? 'page' : undefined}
          >
            {page}
          </button>
        ))}
      </div>
      <button
        type="button"
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        aria-label="Next page"
      >
        Next
      </button>
    </nav>
  )
}

export function DiscoverySessionList() {
  const {
    sessions,
    isLoading,
    error,
    page,
    totalPages,
    setPage,
    createSession,
    deleteSession,
    isCreating,
    isDeleting,
  } = useDiscoverySessions()

  const [sessionToDelete, setSessionToDelete] = useState<DiscoverySession | null>(null)

  const handleCreateSession = useCallback(async () => {
    const name = `New Discovery ${new Date().toLocaleDateString()}`
    await createSession(name)
  }, [createSession])

  const handleDeleteClick = useCallback((session: DiscoverySession) => {
    setSessionToDelete(session)
  }, [])

  const handleConfirmDelete = useCallback(async () => {
    if (sessionToDelete) {
      await deleteSession(sessionToDelete.id)
      setSessionToDelete(null)
    }
  }, [sessionToDelete, deleteSession])

  const handleCancelDelete = useCallback(() => {
    setSessionToDelete(null)
  }, [])

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
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Discovery Sessions</h1>
          <p className="mt-1 text-gray-600">
            Manage your AI opportunity discovery sessions
          </p>
        </div>
        <button
          type="button"
          onClick={handleCreateSession}
          disabled={isCreating}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="New Discovery"
        >
          {isCreating ? 'Creating...' : 'New Discovery'}
        </button>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center p-8" role="status" aria-live="polite">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-500">Loading sessions...</span>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && sessions.length === 0 && (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-500 mb-4">No sessions found</p>
          <button
            type="button"
            onClick={handleCreateSession}
            disabled={isCreating}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Start Your First Discovery
          </button>
        </div>
      )}

      {/* Session List */}
      {!isLoading && sessions.length > 0 && (
        <div className="space-y-4">
          {sessions.map((session) => (
            <SessionCard
              key={session.id}
              session={session}
              onDelete={handleDeleteClick}
              isDeleting={isDeleting === session.id}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {!isLoading && sessions.length > 0 && (
        <Pagination
          currentPage={page}
          totalPages={totalPages}
          onPageChange={setPage}
        />
      )}

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={sessionToDelete !== null}
        sessionName={sessionToDelete?.name || ''}
        onConfirm={handleConfirmDelete}
        onCancel={handleCancelDelete}
        isDeleting={isDeleting !== null}
      />
    </div>
  )
}
