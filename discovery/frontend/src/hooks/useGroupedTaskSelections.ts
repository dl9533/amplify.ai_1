import { useState, useCallback, useEffect, useRef } from 'react'
import {
  tasksApi,
  ApiError,
  GroupedTasksByRoleResponse,
} from '../services'

export interface UseGroupedTaskSelectionsReturn {
  data: GroupedTasksByRoleResponse | null
  isLoading: boolean
  isLoadingTasks: boolean
  isUpdating: boolean
  error: string | null
  toggleTask: (selectionId: string) => Promise<void>
  selectAllForRole: (roleMappingId: string, selected: boolean) => Promise<void>
  selectAllForLob: (lob: string, selected: boolean) => Promise<void>
  refresh: () => Promise<void>
}

export function useGroupedTaskSelections(sessionId?: string): UseGroupedTaskSelectionsReturn {
  const [data, setData] = useState<GroupedTasksByRoleResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingTasks, setIsLoadingTasks] = useState(false)
  const [isUpdating, setIsUpdating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const hasAttemptedLoad = useRef(false)

  const loadTasksFromOnet = useCallback(async () => {
    if (!sessionId) return

    try {
      setIsLoadingTasks(true)
      setError(null)

      await tasksApi.loadForSession(sessionId)
      // After loading, fetch grouped data
      const response = await tasksApi.getGroupedBySourceRole(sessionId)
      setData(response)
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Failed to load tasks from O*NET'
      setError(message)
    } finally {
      setIsLoadingTasks(false)
    }
  }, [sessionId])

  const loadGroupedTasks = useCallback(async (showLoading = true) => {
    if (!sessionId) {
      setData(null)
      setIsLoading(false)
      return
    }

    try {
      if (showLoading) {
        setIsLoading(true)
      }
      setError(null)

      const response = await tasksApi.getGroupedBySourceRole(sessionId)

      // If no tasks exist and we haven't tried loading yet, auto-load from O*NET
      if (response.overall_summary.total_tasks === 0 && !hasAttemptedLoad.current) {
        hasAttemptedLoad.current = true
        setIsLoading(false)
        await loadTasksFromOnet()
        return
      }

      setData(response)
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Failed to load grouped tasks'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }, [sessionId, loadTasksFromOnet])

  useEffect(() => {
    // Reset load attempt flag when session changes
    hasAttemptedLoad.current = false
    loadGroupedTasks()
  }, [loadGroupedTasks])

  const toggleTask = useCallback(async (selectionId: string) => {
    if (!data) return

    // Store previous state for accurate rollback
    const previousData = data

    // Find the current selection state
    let isCurrentlySelected = false
    for (const lobGroup of data.lob_groups) {
      for (const role of lobGroup.roles) {
        const task = role.tasks.find((t) => t.id === selectionId)
        if (task) {
          isCurrentlySelected = task.selected
          break
        }
      }
    }
    for (const role of data.ungrouped_roles) {
      const task = role.tasks.find((t) => t.id === selectionId)
      if (task) {
        isCurrentlySelected = task.selected
        break
      }
    }

    // Optimistic update
    setData((prev) => {
      if (!prev) return prev
      return {
        ...prev,
        overall_summary: {
          ...prev.overall_summary,
          selected_count: prev.overall_summary.selected_count + (isCurrentlySelected ? -1 : 1),
        },
        lob_groups: prev.lob_groups.map((lobGroup) => ({
          ...lobGroup,
          summary: {
            ...lobGroup.summary,
            selected_count: lobGroup.roles.some((role) =>
              role.tasks.some((t) => t.id === selectionId)
            )
              ? lobGroup.summary.selected_count + (isCurrentlySelected ? -1 : 1)
              : lobGroup.summary.selected_count,
          },
          roles: lobGroup.roles.map((role) => ({
            ...role,
            tasks: role.tasks.map((t) =>
              t.id === selectionId
                ? { ...t, selected: !isCurrentlySelected, user_modified: true }
                : t
            ),
          })),
        })),
        ungrouped_roles: prev.ungrouped_roles.map((role) => ({
          ...role,
          tasks: role.tasks.map((t) =>
            t.id === selectionId
              ? { ...t, selected: !isCurrentlySelected, user_modified: true }
              : t
          ),
        })),
      }
    })

    try {
      await tasksApi.updateSelection(selectionId, !isCurrentlySelected)
    } catch (err) {
      // Revert to previous state on error (more reliable than refetching)
      setData(previousData)
      const message =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Failed to update task selection'
      setError(message)
    }
  }, [data])

  const selectAllForRole = useCallback(
    async (roleMappingId: string, selected: boolean) => {
      if (!sessionId || !data) return

      // Find the role to get its task IDs
      let targetRole = null
      for (const lobGroup of data.lob_groups) {
        targetRole = lobGroup.roles.find((r) => r.role_mapping_id === roleMappingId)
        if (targetRole) break
      }
      if (!targetRole) {
        targetRole = data.ungrouped_roles.find((r) => r.role_mapping_id === roleMappingId)
      }
      if (!targetRole) return

      try {
        setIsUpdating(true)
        setError(null)

        // Get all task IDs for this role
        const taskIds = targetRole.tasks.map((t) => t.task_id)
        await tasksApi.bulkUpdate(roleMappingId, taskIds, selected)

        // Refresh to get updated data
        await loadGroupedTasks(false)
      } catch (err) {
        const message =
          err instanceof ApiError
            ? err.message
            : err instanceof Error
              ? err.message
              : 'Failed to bulk update task selections'
        setError(message)
      } finally {
        setIsUpdating(false)
      }
    },
    [sessionId, data, loadGroupedTasks]
  )

  const selectAllForLob = useCallback(
    async (lob: string, selected: boolean) => {
      if (!sessionId || !data) return

      const lobGroup = data.lob_groups.find((g) => g.lob === lob)
      if (!lobGroup) return

      try {
        setIsUpdating(true)
        setError(null)

        // Update all roles in the LOB in parallel
        await Promise.all(
          lobGroup.roles.map((role) => {
            const taskIds = role.tasks.map((t) => t.task_id)
            return tasksApi.bulkUpdate(role.role_mapping_id, taskIds, selected)
          })
        )

        // Refresh to get updated data
        await loadGroupedTasks(false)
      } catch (err) {
        // If any call fails, refresh to show actual state
        await loadGroupedTasks(false)
        const message =
          err instanceof ApiError
            ? err.message
            : err instanceof Error
              ? err.message
              : 'Failed to bulk update LOB task selections'
        setError(message)
      } finally {
        setIsUpdating(false)
      }
    },
    [sessionId, data, loadGroupedTasks]
  )

  return {
    data,
    isLoading,
    isLoadingTasks,
    isUpdating,
    error,
    toggleTask,
    selectAllForRole,
    selectAllForLob,
    refresh: loadGroupedTasks,
  }
}
