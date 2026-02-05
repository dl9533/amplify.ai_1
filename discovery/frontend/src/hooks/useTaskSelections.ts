import { useState, useCallback, useEffect, useRef } from 'react'
import { tasksApi, ApiError } from '../services'

export interface Task {
  id: string
  taskId: number
  description: string | null
  importance: number | null
  selected: boolean
  userModified: boolean
}

export interface RoleMappingWithTasks {
  id: string
  sourceRole: string
  onetCode: string | null
  onetTitle: string | null
  tasks: Task[]
}

/**
 * Transform grouped API response into local state format.
 */
function transformGroupedResponse(
  grouped: Awaited<ReturnType<typeof tasksApi.getGrouped>>
): { mappings: RoleMappingWithTasks[]; selectedIds: Set<string> } {
  const mappings: RoleMappingWithTasks[] = []
  const selectedIds = new Set<string>()

  for (const group of grouped) {
    const tasks: Task[] = group.tasks.map((t) => ({
      id: t.id,
      taskId: t.task_id,
      description: t.description,
      importance: t.importance,
      selected: t.selected,
      userModified: t.user_modified,
    }))

    tasks.forEach((t) => {
      if (t.selected) {
        selectedIds.add(t.id)
      }
    })

    mappings.push({
      id: group.role_mapping_id,
      sourceRole: group.source_role,
      onetCode: group.onet_code,
      onetTitle: group.onet_title,
      tasks,
    })
  }

  return { mappings, selectedIds }
}

export function useTaskSelections(sessionId: string) {
  const [roleMappingsWithTasks, setRoleMappingsWithTasks] = useState<RoleMappingWithTasks[]>([])
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingTasks, setIsLoadingTasks] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const hasAttemptedLoad = useRef(false)

  // Load tasks from O*NET for confirmed role mappings
  const loadTasksFromOnet = useCallback(async () => {
    if (!sessionId) return

    try {
      setIsLoadingTasks(true)
      setError(null)

      const result = await tasksApi.loadForSession(sessionId)

      // After loading, fetch all tasks in a single grouped call
      const grouped = await tasksApi.getGrouped(sessionId)
      const { mappings, selectedIds: newSelectedIds } = transformGroupedResponse(grouped)

      setRoleMappingsWithTasks(mappings)
      setSelectedIds(newSelectedIds)

      return result
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

  const loadTasks = useCallback(async () => {
    if (!sessionId) {
      setRoleMappingsWithTasks([])
      setSelectedIds(new Set())
      setIsLoading(false)
      return
    }

    try {
      setIsLoading(true)
      setError(null)

      // Use the grouped endpoint to fetch all tasks in a single call
      const grouped = await tasksApi.getGrouped(sessionId)

      // If no tasks exist and we haven't tried loading yet, auto-load from O*NET
      const totalTasks = grouped.reduce((sum, g) => sum + g.tasks.length, 0)
      if (totalTasks === 0 && !hasAttemptedLoad.current) {
        hasAttemptedLoad.current = true
        setIsLoading(false)
        await loadTasksFromOnet()
        return
      }

      const { mappings, selectedIds: newSelectedIds } = transformGroupedResponse(grouped)

      setRoleMappingsWithTasks(mappings)
      setSelectedIds(newSelectedIds)
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Failed to load tasks'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }, [sessionId, loadTasksFromOnet])

  useEffect(() => {
    // Reset load attempt flag when session changes
    hasAttemptedLoad.current = false
    loadTasks()
  }, [loadTasks])

  const toggleTask = useCallback(
    async (id: string) => {
      const isCurrentlySelected = selectedIds.has(id)

      // Optimistic update
      setSelectedIds((prev) => {
        const next = new Set(prev)
        if (isCurrentlySelected) {
          next.delete(id)
        } else {
          next.add(id)
        }
        return next
      })

      // Also update in roleMappingsWithTasks
      setRoleMappingsWithTasks((prev) =>
        prev.map((mapping) => ({
          ...mapping,
          tasks: mapping.tasks.map((task) =>
            task.id === id ? { ...task, selected: !isCurrentlySelected, userModified: true } : task
          ),
        }))
      )

      try {
        await tasksApi.updateSelection(id, !isCurrentlySelected)
      } catch (err) {
        // Revert on error
        setSelectedIds((prev) => {
          const next = new Set(prev)
          if (isCurrentlySelected) {
            next.add(id)
          } else {
            next.delete(id)
          }
          return next
        })
        setRoleMappingsWithTasks((prev) =>
          prev.map((mapping) => ({
            ...mapping,
            tasks: mapping.tasks.map((task) =>
              task.id === id ? { ...task, selected: isCurrentlySelected } : task
            ),
          }))
        )
        const message =
          err instanceof ApiError
            ? err.message
            : err instanceof Error
              ? err.message
              : 'Failed to update task selection'
        setError(message)
      }
    },
    [selectedIds]
  )

  const selectAllForMapping = useCallback(
    async (mappingId: string, selected: boolean) => {
      const mapping = roleMappingsWithTasks.find((m) => m.id === mappingId)
      if (!mapping) return

      const taskIds = mapping.tasks.map((t) => t.taskId)
      const selectionIds = mapping.tasks.map((t) => t.id)

      // Optimistic update
      setSelectedIds((prev) => {
        const next = new Set(prev)
        selectionIds.forEach((id) => {
          if (selected) {
            next.add(id)
          } else {
            next.delete(id)
          }
        })
        return next
      })

      setRoleMappingsWithTasks((prev) =>
        prev.map((m) =>
          m.id === mappingId
            ? {
                ...m,
                tasks: m.tasks.map((task) => ({
                  ...task,
                  selected,
                  userModified: true,
                })),
              }
            : m
        )
      )

      try {
        await tasksApi.bulkUpdate(mappingId, taskIds, selected)
      } catch (err) {
        // Revert on error
        setRoleMappingsWithTasks((prev) =>
          prev.map((m) =>
            m.id === mappingId
              ? {
                  ...m,
                  tasks: m.tasks.map((task) => ({
                    ...task,
                    selected: !selected,
                  })),
                }
              : m
          )
        )
        setSelectedIds((prev) => {
          const next = new Set(prev)
          selectionIds.forEach((id) => {
            if (!selected) {
              next.add(id)
            } else {
              next.delete(id)
            }
          })
          return next
        })
        const message =
          err instanceof ApiError
            ? err.message
            : err instanceof Error
              ? err.message
              : 'Failed to bulk update task selections'
        setError(message)
      }
    },
    [roleMappingsWithTasks]
  )

  return {
    roleMappingsWithTasks,
    selectedIds,
    isLoading,
    isLoadingTasks,
    error,
    toggleTask,
    selectAllForMapping,
    refresh: loadTasks,
  }
}
