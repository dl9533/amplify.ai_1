import { useState, useCallback, useEffect } from 'react'
import { adminApi, OnetSyncStatus, OnetSyncResponse, ApiError } from '../services'

export interface UseOnetSyncReturn {
  status: OnetSyncStatus | null
  isLoading: boolean
  isSyncing: boolean
  error: string | null
  syncResult: OnetSyncResponse | null
  triggerSync: (version?: string) => Promise<void>
  refresh: () => Promise<void>
}

export function useOnetSync(): UseOnetSyncReturn {
  const [status, setStatus] = useState<OnetSyncStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSyncing, setIsSyncing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [syncResult, setSyncResult] = useState<OnetSyncResponse | null>(null)

  const loadStatus = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)
      const data = await adminApi.getOnetStatus()
      setStatus(data)
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Failed to load O*NET status'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadStatus()
  }, [loadStatus])

  const triggerSync = useCallback(async (version?: string) => {
    try {
      setIsSyncing(true)
      setError(null)
      setSyncResult(null)

      const result = await adminApi.syncOnet(version)
      setSyncResult(result)

      // Refresh status after sync
      await loadStatus()
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Failed to sync O*NET database'
      setError(message)
      throw err // Re-throw so caller knows it failed
    } finally {
      setIsSyncing(false)
    }
  }, [loadStatus])

  return {
    status,
    isLoading,
    isSyncing,
    error,
    syncResult,
    triggerSync,
    refresh: loadStatus,
  }
}
