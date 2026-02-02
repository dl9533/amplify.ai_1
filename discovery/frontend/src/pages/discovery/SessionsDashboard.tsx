import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AppShell, PageContainer, PageHeader } from '../../components/layout/AppShell'
import { Button, IconButton } from '../../components/ui/Button'
import { ConfirmDialog } from '../../components/ui/Modal'
import { EmptyState, LoadingState, ErrorState } from '../../components/ui/EmptyState'
import { StatusBadge } from '../../components/ui/Badge'
import {
  IconPlus,
  IconTrash,
  IconChevronRight,
  IconTarget,
  IconMoreVertical,
} from '../../components/ui/Icons'
import { useDiscoverySessions } from '../../hooks/useDiscoverySessions'
import { DISCOVERY_STEPS } from '../../components/layout/DiscoveryWizard'

export function SessionsDashboard() {
  const navigate = useNavigate()
  const {
    sessions,
    isLoading,
    error,
    createSession,
    deleteSession,
    isCreating,
    isDeleting,
  } = useDiscoverySessions()

  const [deleteTarget, setDeleteTarget] = useState<string | null>(null)
  const [menuOpen, setMenuOpen] = useState<string | null>(null)

  const handleCreateSession = async () => {
    const session = await createSession()
    if (session) {
      navigate(`/discovery/${session.id}/upload`)
    }
  }

  const handleDeleteSession = async () => {
    if (deleteTarget) {
      await deleteSession(deleteTarget)
      setDeleteTarget(null)
    }
  }

  const handleOpenSession = (sessionId: string, currentStep: number) => {
    const step = DISCOVERY_STEPS[Math.min(currentStep - 1, DISCOVERY_STEPS.length - 1)]
    navigate(`/discovery/${sessionId}/${step.path}`)
  }

  // Format relative time
  const formatRelativeTime = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  return (
    <AppShell>
      <PageContainer size="xl">
        <PageHeader
          title="Discovery Sessions"
          description="Identify and prioritize automation opportunities across your workforce"
          actions={
            <Button
              variant="primary"
              size="md"
              icon={<IconPlus size={18} />}
              onClick={handleCreateSession}
              loading={isCreating}
            >
              New Session
            </Button>
          }
        />

        {/* Content */}
        {isLoading ? (
          <LoadingState message="Loading sessions..." />
        ) : error ? (
          <ErrorState
            message={error}
            retry={() => window.location.reload()}
          />
        ) : sessions.length === 0 ? (
          <EmptyState
            icon={<IconTarget size={28} />}
            title="No discovery sessions yet"
            description="Create your first session to start identifying automation opportunities in your organization."
            action={
              <Button
                variant="primary"
                size="md"
                icon={<IconPlus size={18} />}
                onClick={handleCreateSession}
                loading={isCreating}
              >
                Create First Session
              </Button>
            }
          />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {sessions.map((session, index) => (
              <div
                key={session.id}
                className={`
                  surface-interactive group
                  animate-slide-up stagger-${Math.min(index + 1, 6)}
                `}
                style={{ animationFillMode: 'backwards' }}
              >
                <div className="p-5">
                  {/* Header */}
                  <div className="flex items-start justify-between mb-4">
                    <StatusBadge status={session.status as 'draft' | 'in_progress' | 'completed'} />
                    <div className="relative">
                      <IconButton
                        variant="ghost"
                        size="sm"
                        label="Session options"
                        onClick={(e) => {
                          e.stopPropagation()
                          setMenuOpen(menuOpen === session.id ? null : session.id)
                        }}
                        className="opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <IconMoreVertical size={16} />
                      </IconButton>

                      {/* Dropdown menu */}
                      {menuOpen === session.id && (
                        <>
                          <div
                            className="fixed inset-0 z-10"
                            onClick={() => setMenuOpen(null)}
                          />
                          <div className="dropdown-menu right-0 top-full mt-1 z-20">
                            <button
                              className="dropdown-item text-destructive"
                              onClick={(e) => {
                                e.stopPropagation()
                                setDeleteTarget(session.id)
                                setMenuOpen(null)
                              }}
                            >
                              <IconTrash size={16} />
                              Delete session
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Session name */}
                  <h3 className="font-display font-semibold text-default mb-1 truncate">
                    {session.name || `Session ${session.id.slice(0, 8)}`}
                  </h3>

                  {/* Progress */}
                  <div className="flex items-center gap-2 mb-4">
                    <div className="flex-1 h-1.5 bg-bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-accent rounded-full transition-all duration-500"
                        style={{ width: `${(session.currentStep / 5) * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-muted tabular-nums">
                      {session.currentStep}/5
                    </span>
                  </div>

                  {/* Footer */}
                  <div className="flex items-center justify-between pt-3 border-t border-border">
                    <span className="text-xs text-muted">
                      Updated {formatRelativeTime(session.updatedAt)}
                    </span>
                    <button
                      onClick={() => handleOpenSession(session.id, session.currentStep)}
                      className="btn-ghost btn-sm text-accent"
                    >
                      Continue
                      <IconChevronRight size={16} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Delete confirmation dialog */}
        <ConfirmDialog
          isOpen={!!deleteTarget}
          onClose={() => setDeleteTarget(null)}
          onConfirm={handleDeleteSession}
          title="Delete session?"
          description="This will permanently delete the session and all its data. This action cannot be undone."
          confirmLabel="Delete"
          variant="destructive"
          loading={isDeleting}
        />
      </PageContainer>
    </AppShell>
  )
}
