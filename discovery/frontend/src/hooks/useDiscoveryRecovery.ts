import { useState, useCallback, useRef, useEffect } from 'react'

export interface UseDiscoveryRecoveryOptions<T> {
  /** Initial state to use */
  initialState: T
  /** Optional callback when recovery is attempted */
  onRecoveryAttempt?: () => void
}

export interface UseDiscoveryRecoveryReturn<T> {
  /** Current state value */
  currentState: T
  /** The last known good state before an error occurred */
  lastKnownGoodState: T | null
  /** Update the current state (also saves as last known good) */
  updateState: (newState: T) => void
  /** Attempt to recover by restoring the last known good state */
  attemptRecovery: () => boolean
  /** Mark the current state as valid (saves snapshot) */
  saveCheckpoint: () => void
  /** Whether recovery is available */
  canRecover: boolean
  /** Reset to initial state */
  reset: () => void
}

/**
 * Hook to provide recovery utilities for discovery sessions.
 * Maintains a snapshot of the last known good state that can be
 * restored in case of errors.
 */
export function useDiscoveryRecovery<T>(
  options: UseDiscoveryRecoveryOptions<T>
): UseDiscoveryRecoveryReturn<T> {
  const { initialState, onRecoveryAttempt } = options

  const [currentState, setCurrentState] = useState<T>(initialState)
  const lastKnownGoodStateRef = useRef<T | null>(null)

  // Save the initial state as the first checkpoint
  useEffect(() => {
    if (lastKnownGoodStateRef.current === null) {
      lastKnownGoodStateRef.current = initialState
    }
  }, [initialState])

  const updateState = useCallback((newState: T) => {
    // Save current state as last known good before updating
    setCurrentState((prev) => {
      lastKnownGoodStateRef.current = prev
      return newState
    })
  }, [])

  const saveCheckpoint = useCallback(() => {
    lastKnownGoodStateRef.current = currentState
  }, [currentState])

  const attemptRecovery = useCallback((): boolean => {
    if (lastKnownGoodStateRef.current !== null) {
      onRecoveryAttempt?.()
      setCurrentState(lastKnownGoodStateRef.current)
      return true
    }
    return false
  }, [onRecoveryAttempt])

  const reset = useCallback(() => {
    setCurrentState(initialState)
    lastKnownGoodStateRef.current = initialState
  }, [initialState])

  const canRecover = lastKnownGoodStateRef.current !== null

  return {
    currentState,
    lastKnownGoodState: lastKnownGoodStateRef.current,
    updateState,
    attemptRecovery,
    saveCheckpoint,
    canRecover,
    reset,
  }
}
