import { useState, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import { AppShell } from '../../components/layout/AppShell'
import { DiscoveryWizard, StepContent } from '../../components/layout/DiscoveryWizard'
import { Button } from '../../components/ui/Button'
import { LoadingState, ErrorState } from '../../components/ui/EmptyState'
import {
  IconChevronDown,
  IconChevronUp,
  IconCheck,
  IconCheckAll,
} from '../../components/ui/Icons'
import { useTaskSelections } from '../../hooks/useTaskSelections'

export function ActivitiesStep() {
  const { sessionId } = useParams()
  const {
    roleMappingsWithTasks,
    selectedIds,
    isLoading,
    error,
    toggleTask,
    selectAllForMapping,
  } = useTaskSelections(sessionId || '')

  const [expandedMappings, setExpandedMappings] = useState<Set<string>>(new Set())

  // Calculate stats
  const stats = useMemo(() => {
    let totalTasks = 0
    let selectedTasks = selectedIds.size

    roleMappingsWithTasks.forEach((mapping) => {
      totalTasks += mapping.tasks.length
    })

    return { totalTasks, selectedTasks }
  }, [roleMappingsWithTasks, selectedIds])

  const toggleMapping = (mappingId: string) => {
    setExpandedMappings((prev) => {
      const next = new Set(prev)
      if (next.has(mappingId)) {
        next.delete(mappingId)
      } else {
        next.add(mappingId)
      }
      return next
    })
  }

  const handleSelectAll = async (mappingId: string) => {
    const mapping = roleMappingsWithTasks.find((m) => m.id === mappingId)
    if (!mapping) return

    // If all are selected, deselect all; otherwise, select all
    const allSelected = mapping.tasks.every((t) => selectedIds.has(t.id))
    await selectAllForMapping(mappingId, !allSelected)
  }

  const canProceed = stats.selectedTasks > 0

  if (isLoading) {
    return (
      <AppShell>
        <DiscoveryWizard currentStep={3}>
          <LoadingState message="Loading tasks..." />
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
          description="Review the O*NET tasks for each confirmed role. All tasks are selected by default. Deselect any tasks that don't apply to your organization."
        >
          {/* Summary stats */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="surface p-4 text-center">
              <p className="text-2xl font-display font-bold text-default">
                {stats.selectedTasks}
              </p>
              <p className="text-xs text-muted">Tasks Selected</p>
            </div>
            <div className="surface p-4 text-center">
              <p className="text-2xl font-display font-bold text-default">
                {stats.totalTasks}
              </p>
              <p className="text-xs text-muted">Total Tasks</p>
            </div>
            <div className="surface p-4 text-center">
              <p className="text-2xl font-display font-bold text-default">
                {roleMappingsWithTasks.length}
              </p>
              <p className="text-xs text-muted">Roles</p>
            </div>
          </div>

          {/* Role mapping accordion list */}
          <div className="space-y-3">
            {roleMappingsWithTasks.map((mapping, mappingIndex) => {
              const isExpanded = expandedMappings.has(mapping.id)
              const selectedInMapping = mapping.tasks.filter((t) => selectedIds.has(t.id)).length
              const totalInMapping = mapping.tasks.length
              const allSelected = totalInMapping > 0 && selectedInMapping === totalInMapping

              return (
                <div
                  key={mapping.id}
                  className="surface overflow-hidden animate-slide-up"
                  style={{ animationDelay: `${Math.min(mappingIndex, 8) * 50}ms` }}
                >
                  {/* Role mapping header */}
                  <div className="flex items-center">
                    <button
                      onClick={() => toggleMapping(mapping.id)}
                      className="flex-1 p-4 flex items-center gap-4 text-left hover:bg-bg-muted/50 transition-colors"
                    >
                      {/* Expand icon */}
                      <div className="shrink-0 text-muted">
                        {isExpanded ? (
                          <IconChevronUp size={20} />
                        ) : (
                          <IconChevronDown size={20} />
                        )}
                      </div>

                      {/* Role info */}
                      <div className="flex-1 min-w-0">
                        <h4 className="font-display font-medium text-default truncate">
                          {mapping.sourceRole}
                        </h4>
                        <div className="flex items-center gap-3 mt-1">
                          <span className="text-xs text-muted">
                            {mapping.onetTitle || mapping.onetCode}
                          </span>
                          <span className="text-xs text-subtle">
                            {selectedInMapping}/{totalInMapping} tasks selected
                          </span>
                        </div>
                      </div>

                      {/* Selection progress ring */}
                      <div className="shrink-0 w-10 h-10 relative">
                        <svg className="w-10 h-10 -rotate-90">
                          <circle
                            cx="20"
                            cy="20"
                            r="16"
                            fill="none"
                            strokeWidth="3"
                            className="stroke-bg-muted"
                          />
                          <circle
                            cx="20"
                            cy="20"
                            r="16"
                            fill="none"
                            strokeWidth="3"
                            strokeDasharray={`${totalInMapping > 0 ? (selectedInMapping / totalInMapping) * 100.53 : 0} 100.53`}
                            className="stroke-accent transition-all duration-300"
                          />
                        </svg>
                        <span className="absolute inset-0 flex items-center justify-center text-xs font-medium text-muted">
                          {selectedInMapping}
                        </span>
                      </div>
                    </button>

                    {/* Select all button */}
                    {isExpanded && totalInMapping > 0 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="mr-2"
                        icon={<IconCheckAll size={16} />}
                        onClick={() => handleSelectAll(mapping.id)}
                      >
                        {allSelected ? 'Deselect All' : 'Select All'}
                      </Button>
                    )}
                  </div>

                  {/* Task list (expanded) */}
                  {isExpanded && (
                    <div className="border-t border-border">
                      {mapping.tasks.length === 0 ? (
                        <div className="p-4 text-center text-muted text-sm">
                          No tasks found for this occupation.
                        </div>
                      ) : (
                        mapping.tasks.map((task) => {
                          const isSelected = selectedIds.has(task.id)

                          return (
                            <label
                              key={task.id}
                              className={`
                                flex items-start gap-3 p-4 cursor-pointer
                                border-b border-border last:border-0
                                hover:bg-bg-muted/50 transition-colors
                                ${isSelected ? 'bg-accent/5' : ''}
                              `}
                            >
                              {/* Checkbox */}
                              <div className="relative shrink-0 mt-0.5">
                                <input
                                  type="checkbox"
                                  checked={isSelected}
                                  onChange={() => toggleTask(task.id)}
                                  className="sr-only peer"
                                />
                                <div
                                  className={`
                                    w-5 h-5 rounded border-2 flex items-center justify-center
                                    transition-all duration-150
                                    ${
                                      isSelected
                                        ? 'bg-accent border-accent'
                                        : 'border-border bg-bg-muted'
                                    }
                                  `}
                                >
                                  {isSelected && (
                                    <IconCheck size={12} className="text-white" />
                                  )}
                                </div>
                              </div>

                              {/* Task content */}
                              <div className="flex-1 min-w-0">
                                <p
                                  className={`
                                    text-sm
                                    ${isSelected ? 'text-default' : 'text-muted'}
                                  `}
                                >
                                  {task.description || 'No description available'}
                                </p>
                                {task.importance !== null && (
                                  <p className="text-xs text-subtle mt-1">
                                    Importance: {task.importance.toFixed(1)}
                                  </p>
                                )}
                              </div>
                            </label>
                          )
                        })
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {/* Empty state */}
          {roleMappingsWithTasks.length === 0 && (
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
