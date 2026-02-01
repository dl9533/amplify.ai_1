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
  const [lastKnownGoodState, setLastKnownGoodState] = useState<T | null>(initialState)

  // Track current state in a ref for use in callbacks to avoid stale closures
  const currentStateRef = useRef<T>(initialState)

  // Keep currentStateRef in sync with currentState
  useEffect(() => {
    currentStateRef.current = currentState
  }, [currentState])

  const updateState = useCallback((newState: T) => {
    // Capture current state BEFORE calling setCurrentState
    // This avoids stale closure issues
    const previousState = currentStateRef.current
    setLastKnownGoodState(previousState)
    setCurrentState(newState)
  }, [])

  const saveCheckpoint = useCallback(() => {
    setLastKnownGoodState(currentStateRef.current)
  }, [])

  const attemptRecovery = useCallback((): boolean => {
    if (lastKnownGoodState !== null) {
      onRecoveryAttempt?.()
      setCurrentState(lastKnownGoodState)
      return true
    }
    return false
  }, [lastKnownGoodState, onRecoveryAttempt])

  const reset = useCallback(() => {
    setCurrentState(initialState)
    setLastKnownGoodState(initialState)
  }, [initialState])

  const canRecover = lastKnownGoodState !== null

  return {
    currentState,
    lastKnownGoodState,
    updateState,
    attemptRecovery,
    saveCheckpoint,
    canRecover,
    reset,
  }
}
