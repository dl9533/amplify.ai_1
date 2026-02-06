import { useState, useCallback } from 'react'
import { Button } from '../../ui/Button'
import {
  IconChevronDown,
  IconChevronRight,
  IconCheck,
  IconCheckAll,
  IconUsers,
} from '../../ui/Icons'
import { ScoreBar } from '../../ui/ScoreBar'
import type {
  GroupedTasksResponse,
  LobTaskGroup,
  OnetTaskGroup,
  TaskResponse,
} from '../../../services/discoveryApi'

export interface GroupedTasksViewProps {
  data: GroupedTasksResponse
  onToggleTask: (selectionId: string) => void
  onSelectAllForOccupation: (onetCode: string, selected: boolean, lob?: string) => void
  onSelectAllForLob: (lob: string, selected: boolean) => void
  isUpdating?: boolean
}

export function GroupedTasksView({
  data,
  onToggleTask,
  onSelectAllForOccupation,
  onSelectAllForLob,
  isUpdating = false,
}: GroupedTasksViewProps) {
  const { overall_summary, lob_groups, ungrouped_occupations } = data

  // Track which LOB groups and occupations are expanded
  const [expandedLobs, setExpandedLobs] = useState<Set<string>>(new Set())
  const [expandedOccupations, setExpandedOccupations] = useState<Set<string>>(new Set())

  const toggleLobExpanded = useCallback((lob: string) => {
    setExpandedLobs((prev) => {
      const next = new Set(prev)
      if (next.has(lob)) {
        next.delete(lob)
      } else {
        next.add(lob)
      }
      return next
    })
  }, [])

  const toggleOccupationExpanded = useCallback((key: string) => {
    setExpandedOccupations((prev) => {
      const next = new Set(prev)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      return next
    })
  }, [])

  const selectionRate = overall_summary.total_tasks > 0
    ? overall_summary.selected_count / overall_summary.total_tasks
    : 0

  return (
    <div className="space-y-6">
      {/* Overall summary card */}
      <div className="surface p-5 rounded-lg">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-display font-semibold text-default">Task Selection Summary</h2>
            <p className="text-sm text-muted">
              {overall_summary.occupation_count} occupations · {overall_summary.total_employees.toLocaleString()} employees
            </p>
          </div>
        </div>

        {/* Progress bar */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm text-muted">Selection Progress</span>
            <span className="text-sm font-medium text-default">
              {overall_summary.selected_count} / {overall_summary.total_tasks} tasks
            </span>
          </div>
          <ScoreBar value={selectionRate} variant="success" size="lg" />
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-3 gap-4">
          <StatCard
            label="Total Tasks"
            value={overall_summary.total_tasks}
          />
          <StatCard
            label="Selected"
            value={overall_summary.selected_count}
            variant="success"
          />
          <StatCard
            label="Occupations"
            value={overall_summary.occupation_count}
          />
        </div>
      </div>

      {/* LOB groups */}
      {lob_groups.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-muted uppercase tracking-wide">
            By Line of Business ({lob_groups.length})
          </h3>
          {lob_groups.map((group) => (
            <LobTaskGroupCard
              key={group.lob}
              group={group}
              isExpanded={expandedLobs.has(group.lob)}
              onToggleExpanded={() => toggleLobExpanded(group.lob)}
              expandedOccupations={expandedOccupations}
              onToggleOccupation={toggleOccupationExpanded}
              onToggleTask={onToggleTask}
              onSelectAllForOccupation={onSelectAllForOccupation}
              onSelectAllForLob={onSelectAllForLob}
              isUpdating={isUpdating}
            />
          ))}
        </div>
      )}

      {/* Ungrouped occupations */}
      {ungrouped_occupations.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-muted uppercase tracking-wide">
            Ungrouped Occupations ({ungrouped_occupations.length})
          </h3>
          <div className="surface rounded-lg divide-y divide-border">
            {ungrouped_occupations.map((occupation) => {
              const key = `ungrouped-${occupation.onet_code}`
              return (
                <OccupationTaskCard
                  key={key}
                  occupation={occupation}
                  isExpanded={expandedOccupations.has(key)}
                  onToggleExpanded={() => toggleOccupationExpanded(key)}
                  onToggleTask={onToggleTask}
                  onSelectAll={(selected) => onSelectAllForOccupation(occupation.onet_code, selected)}
                  isUpdating={isUpdating}
                />
              )
            })}
          </div>
        </div>
      )}

      {/* Empty state */}
      {lob_groups.length === 0 && ungrouped_occupations.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted">No tasks found. Please confirm role mappings first.</p>
        </div>
      )}
    </div>
  )
}

interface StatCardProps {
  label: string
  value: number
  variant?: 'default' | 'success' | 'warning' | 'error'
}

function StatCard({ label, value, variant = 'default' }: StatCardProps) {
  const variantClasses = {
    default: 'text-default',
    success: 'text-success',
    warning: 'text-warning',
    error: 'text-error',
  }

  return (
    <div className="p-3 bg-bg-muted rounded-lg">
      <span className="text-xs text-muted uppercase tracking-wide">{label}</span>
      <p className={`text-2xl font-bold ${variantClasses[variant]}`}>{value}</p>
    </div>
  )
}

interface LobTaskGroupCardProps {
  group: LobTaskGroup
  isExpanded: boolean
  onToggleExpanded: () => void
  expandedOccupations: Set<string>
  onToggleOccupation: (key: string) => void
  onToggleTask: (selectionId: string) => void
  onSelectAllForOccupation: (onetCode: string, selected: boolean, lob?: string) => void
  onSelectAllForLob: (lob: string, selected: boolean) => void
  isUpdating?: boolean
}

function LobTaskGroupCard({
  group,
  isExpanded,
  onToggleExpanded,
  expandedOccupations,
  onToggleOccupation,
  onToggleTask,
  onSelectAllForOccupation,
  onSelectAllForLob,
  isUpdating = false,
}: LobTaskGroupCardProps) {
  const { summary, occupations, lob } = group

  const selectionRate = summary.total_tasks > 0
    ? summary.selected_count / summary.total_tasks
    : 0

  const allSelected = summary.selected_count === summary.total_tasks && summary.total_tasks > 0

  return (
    <div className="surface rounded-lg overflow-hidden">
      {/* Header - always visible */}
      <button
        onClick={onToggleExpanded}
        className="w-full p-4 flex items-center justify-between hover:bg-bg-muted/50 transition-colors"
        aria-expanded={isExpanded}
      >
        <div className="flex items-center gap-3">
          <span className="text-muted">
            {isExpanded ? <IconChevronDown size={20} /> : <IconChevronRight size={20} />}
          </span>
          <div className="text-left">
            <h3 className="font-display font-semibold text-default">{lob}</h3>
            <p className="text-sm text-muted">
              {summary.occupation_count} occupations · {summary.total_employees.toLocaleString()} employees
            </p>
          </div>
        </div>

        {/* Summary stats */}
        <div className="flex items-center gap-6">
          <div className="text-right">
            <p className="text-sm font-medium text-default">
              {summary.selected_count}/{summary.total_tasks}
            </p>
            <p className="text-xs text-muted">tasks selected</p>
          </div>
          <div className="w-24">
            <ScoreBar value={selectionRate} variant="success" />
          </div>
        </div>
      </button>

      {/* Expanded content */}
      {isExpanded && (
        <div className="border-t border-border">
          {/* Bulk actions for LOB */}
          <div className="p-3 bg-bg-muted/50 flex items-center justify-between">
            <span className="text-sm text-muted">
              {summary.occupation_count} occupations in this LOB
            </span>
            <Button
              variant="secondary"
              size="sm"
              icon={<IconCheckAll size={14} />}
              onClick={() => onSelectAllForLob(lob, !allSelected)}
              disabled={isUpdating}
            >
              {allSelected ? 'Deselect All' : 'Select All'}
            </Button>
          </div>

          {/* Occupations list */}
          <div className="divide-y divide-border">
            {occupations.map((occupation) => {
              const key = `${lob}-${occupation.onet_code}`
              return (
                <OccupationTaskCard
                  key={key}
                  occupation={occupation}
                  lob={lob}
                  isExpanded={expandedOccupations.has(key)}
                  onToggleExpanded={() => onToggleOccupation(key)}
                  onToggleTask={onToggleTask}
                  onSelectAll={(selected) => onSelectAllForOccupation(occupation.onet_code, selected, lob)}
                  isUpdating={isUpdating}
                />
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

interface OccupationTaskCardProps {
  occupation: OnetTaskGroup
  lob?: string
  isExpanded: boolean
  onToggleExpanded: () => void
  onToggleTask: (selectionId: string) => void
  onSelectAll: (selected: boolean) => void
  isUpdating?: boolean
}

function OccupationTaskCard({
  occupation,
  lob: _lob,
  isExpanded,
  onToggleExpanded,
  onToggleTask,
  onSelectAll,
  isUpdating = false,
}: OccupationTaskCardProps) {
  const selectedCount = occupation.tasks.filter((t) => t.selected).length
  const totalCount = occupation.tasks.length
  const allSelected = selectedCount === totalCount && totalCount > 0
  const selectionRate = totalCount > 0 ? selectedCount / totalCount : 0

  return (
    <div className="bg-elevated/30">
      {/* Occupation header */}
      <div className="flex items-center">
        <button
          onClick={onToggleExpanded}
          className="flex-1 p-4 flex items-center gap-4 text-left hover:bg-bg-muted/50 transition-colors"
          aria-expanded={isExpanded}
        >
          {/* Expand icon */}
          <div className="shrink-0 text-muted">
            {isExpanded ? <IconChevronDown size={18} /> : <IconChevronRight size={18} />}
          </div>

          {/* Occupation info */}
          <div className="flex-1 min-w-0">
            <h4 className="font-display font-medium text-default truncate">
              {occupation.onet_title}
            </h4>
            <div className="flex items-center gap-3 mt-1">
              <span className="text-xs text-muted">{occupation.onet_code}</span>
              {occupation.source_roles.length > 1 && (
                <span className="text-xs text-subtle">
                  ({occupation.source_roles.length} roles)
                </span>
              )}
              <div className="flex items-center gap-1 text-muted">
                <IconUsers size={12} />
                <span className="text-xs">{occupation.employee_count}</span>
              </div>
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
                strokeDasharray={`${selectionRate * 100.53} 100.53`}
                className="stroke-accent transition-all duration-300"
              />
            </svg>
            <span className="absolute inset-0 flex items-center justify-center text-xs font-medium text-muted">
              {selectedCount}
            </span>
          </div>
        </button>

        {/* Select all button */}
        {isExpanded && totalCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            className="mr-2"
            icon={<IconCheckAll size={16} />}
            onClick={() => onSelectAll(!allSelected)}
            disabled={isUpdating}
          >
            {allSelected ? 'Deselect All' : 'Select All'}
          </Button>
        )}
      </div>

      {/* Task list (expanded) */}
      {isExpanded && (
        <div className="border-t border-border">
          {occupation.source_roles.length > 1 && (
            <div className="px-4 py-2 bg-info/5 text-xs text-info">
              Tasks shared by: {occupation.source_roles.join(', ')}
            </div>
          )}
          {totalCount === 0 ? (
            <div className="p-4 text-center text-muted text-sm">
              No tasks found for this occupation.
            </div>
          ) : (
            occupation.tasks.map((task) => (
              <TaskRow
                key={task.id}
                task={task}
                onToggle={() => onToggleTask(task.id)}
              />
            ))
          )}
        </div>
      )}
    </div>
  )
}

interface TaskRowProps {
  task: TaskResponse
  onToggle: () => void
}

function TaskRow({ task, onToggle }: TaskRowProps) {
  return (
    <label
      className={`
        flex items-start gap-3 p-4 cursor-pointer
        border-b border-border last:border-0
        hover:bg-bg-muted/50 transition-colors
        ${task.selected ? 'bg-accent/5' : ''}
      `}
    >
      {/* Checkbox */}
      <div className="relative shrink-0 mt-0.5">
        <input
          type="checkbox"
          checked={task.selected}
          onChange={onToggle}
          className="sr-only peer"
        />
        <div
          className={`
            w-5 h-5 rounded border-2 flex items-center justify-center
            transition-all duration-150
            ${task.selected
              ? 'bg-accent border-accent'
              : 'border-border bg-bg-muted'
            }
          `}
        >
          {task.selected && (
            <IconCheck size={12} className="text-white" />
          )}
        </div>
      </div>

      {/* Task content */}
      <div className="flex-1 min-w-0">
        <p
          className={`
            text-sm
            ${task.selected ? 'text-default' : 'text-muted'}
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
}
