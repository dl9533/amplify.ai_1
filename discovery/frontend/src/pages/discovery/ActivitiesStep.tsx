import { useParams } from 'react-router-dom'
import { AppShell } from '../../components/layout/AppShell'
import { DiscoveryWizard, StepContent } from '../../components/layout/DiscoveryWizard'
import { LoadingState, ErrorState } from '../../components/ui/EmptyState'
import { GroupedTasksView } from '../../components/features/discovery/GroupedTasksView'
import { useGroupedTaskSelections } from '../../hooks/useGroupedTaskSelections'

export function ActivitiesStep() {
  const { sessionId } = useParams()
  const {
    data,
    isLoading,
    isLoadingTasks,
    isUpdating,
    error,
    toggleTask,
    selectAllForRole,
    selectAllForLob,
  } = useGroupedTaskSelections(sessionId || '')

  const canProceed = data ? data.overall_summary.selected_count > 0 : false

  if (isLoading || isLoadingTasks) {
    return (
      <AppShell>
        <DiscoveryWizard currentStep={3}>
          <LoadingState
            message={isLoadingTasks
              ? "Loading tasks from O*NET... This may take a moment."
              : "Loading tasks..."
            }
          />
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
          title="Review Tasks"
          description="Review the O*NET tasks for each role. Tasks are grouped by Line of Business and organizational role. All tasks are selected by default. Deselect any tasks that don't apply to your organization."
        >
          {data ? (
            <GroupedTasksView
              data={data}
              onToggleTask={toggleTask}
              onSelectAllForRole={selectAllForRole}
              onSelectAllForLob={selectAllForLob}
              isUpdating={isUpdating}
            />
          ) : (
            <div className="text-center py-12">
              <p className="text-muted">
                No tasks found. Please complete role mapping first.
              </p>
            </div>
          )}
        </StepContent>
      </DiscoveryWizard>
    </AppShell>
  )
}
