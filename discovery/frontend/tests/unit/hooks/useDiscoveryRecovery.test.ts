import { renderHook, act, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useDiscoveryRecovery } from '@/hooks/useDiscoveryRecovery'

describe('useDiscoveryRecovery', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('initial state', () => {
    it('initializes with the provided initial state', () => {
      const initialState = { step: 1, data: 'test' }

      const { result } = renderHook(() =>
        useDiscoveryRecovery({ initialState })
      )

      expect(result.current.currentState).toEqual(initialState)
    })

    it('sets lastKnownGoodState to initial state after effect runs', async () => {
      const initialState = { value: 'initial' }

      const { result } = renderHook(() =>
        useDiscoveryRecovery({ initialState })
      )

      // Wait for the useEffect to set lastKnownGoodState
      await waitFor(() => {
        expect(result.current.lastKnownGoodState).toEqual(initialState)
      })
    })

    it('canRecover is true after initial effect runs', async () => {
      const initialState = { value: 'test' }

      const { result } = renderHook(() =>
        useDiscoveryRecovery({ initialState })
      )

      // Wait for the useEffect to set lastKnownGoodState
      await waitFor(() => {
        expect(result.current.canRecover).toBe(true)
      })
    })

    it('returns all expected properties and methods', () => {
      const { result } = renderHook(() =>
        useDiscoveryRecovery({ initialState: {} })
      )

      expect(result.current).toHaveProperty('currentState')
      expect(result.current).toHaveProperty('lastKnownGoodState')
      expect(result.current).toHaveProperty('updateState')
      expect(result.current).toHaveProperty('attemptRecovery')
      expect(result.current).toHaveProperty('saveCheckpoint')
      expect(result.current).toHaveProperty('canRecover')
      expect(result.current).toHaveProperty('reset')
      expect(typeof result.current.updateState).toBe('function')
      expect(typeof result.current.attemptRecovery).toBe('function')
      expect(typeof result.current.saveCheckpoint).toBe('function')
      expect(typeof result.current.reset).toBe('function')
    })
  })

  describe('updateState', () => {
    it('updates current state to new value', () => {
      const initialState = { step: 1 }
      const newState = { step: 2 }

      const { result } = renderHook(() =>
        useDiscoveryRecovery({ initialState })
      )

      act(() => {
        result.current.updateState(newState)
      })

      expect(result.current.currentState).toEqual(newState)
    })

    it('saves previous state as lastKnownGoodState before updating', async () => {
      const initialState = { step: 1 }
      const secondState = { step: 2 }
      const thirdState = { step: 3 }

      const { result } = renderHook(() =>
        useDiscoveryRecovery({ initialState })
      )

      // Wait for initial effect to run
      await waitFor(() => {
        expect(result.current.lastKnownGoodState).toEqual(initialState)
      })

      // First update
      act(() => {
        result.current.updateState(secondState)
      })

      expect(result.current.currentState).toEqual(secondState)
      expect(result.current.lastKnownGoodState).toEqual(initialState)

      // Second update - previous state (secondState) should be saved
      act(() => {
        result.current.updateState(thirdState)
      })

      expect(result.current.currentState).toEqual(thirdState)
      expect(result.current.lastKnownGoodState).toEqual(secondState)
    })

    it('handles multiple rapid updates correctly', () => {
      const initialState = { count: 0 }

      const { result } = renderHook(() =>
        useDiscoveryRecovery({ initialState })
      )

      act(() => {
        result.current.updateState({ count: 1 })
        result.current.updateState({ count: 2 })
        result.current.updateState({ count: 3 })
      })

      expect(result.current.currentState).toEqual({ count: 3 })
    })

    it('works with primitive types', async () => {
      const { result } = renderHook(() =>
        useDiscoveryRecovery({ initialState: 'initial' })
      )

      // Wait for initial effect
      await waitFor(() => {
        expect(result.current.lastKnownGoodState).toBe('initial')
      })

      act(() => {
        result.current.updateState('updated')
      })

      expect(result.current.currentState).toBe('updated')
      expect(result.current.lastKnownGoodState).toBe('initial')
    })

    it('works with arrays', async () => {
      const { result } = renderHook(() =>
        useDiscoveryRecovery({ initialState: [1, 2, 3] })
      )

      // Wait for initial effect
      await waitFor(() => {
        expect(result.current.lastKnownGoodState).toEqual([1, 2, 3])
      })

      act(() => {
        result.current.updateState([4, 5, 6])
      })

      expect(result.current.currentState).toEqual([4, 5, 6])
      expect(result.current.lastKnownGoodState).toEqual([1, 2, 3])
    })
  })

  describe('saveCheckpoint', () => {
    it('saves current state as lastKnownGoodState', async () => {
      const initialState = { step: 1 }
      const newState = { step: 2 }

      const { result } = renderHook(() =>
        useDiscoveryRecovery({ initialState })
      )

      // Wait for initial effects to run
      await waitFor(() => {
        expect(result.current.lastKnownGoodState).toEqual(initialState)
      })

      // Update state (which saves initial as lastKnownGood)
      act(() => {
        result.current.updateState(newState)
      })

      // At this point, lastKnownGood is initialState
      expect(result.current.lastKnownGoodState).toEqual(initialState)

      // Now save checkpoint - should save newState as lastKnownGood
      act(() => {
        result.current.saveCheckpoint()
      })

      expect(result.current.lastKnownGoodState).toEqual(newState)
    })

    it('can be called multiple times', async () => {
      const { result } = renderHook(() =>
        useDiscoveryRecovery({ initialState: { value: 'a' } })
      )

      // Wait for initial effects
      await waitFor(() => {
        expect(result.current.canRecover).toBe(true)
      })

      act(() => {
        result.current.updateState({ value: 'b' })
      })

      act(() => {
        result.current.saveCheckpoint()
      })

      expect(result.current.lastKnownGoodState).toEqual({ value: 'b' })

      act(() => {
        result.current.updateState({ value: 'c' })
      })

      act(() => {
        result.current.saveCheckpoint()
      })

      expect(result.current.lastKnownGoodState).toEqual({ value: 'c' })
    })
  })

  describe('attemptRecovery', () => {
    it('restores lastKnownGoodState and returns true when available', async () => {
      const initialState = { step: 1 }
      const newState = { step: 2 }

      const { result } = renderHook(() =>
        useDiscoveryRecovery({ initialState })
      )

      // Wait for initial effect
      await waitFor(() => {
        expect(result.current.lastKnownGoodState).toEqual(initialState)
      })

      // Update to new state
      act(() => {
        result.current.updateState(newState)
      })

      expect(result.current.currentState).toEqual(newState)
      expect(result.current.lastKnownGoodState).toEqual(initialState)

      // Attempt recovery
      let recovered: boolean
      act(() => {
        recovered = result.current.attemptRecovery()
      })

      expect(recovered!).toBe(true)
      expect(result.current.currentState).toEqual(initialState)
    })

    it('calls onRecoveryAttempt callback when provided', async () => {
      const onRecoveryAttempt = vi.fn()
      const initialState = { step: 1 }

      const { result } = renderHook(() =>
        useDiscoveryRecovery({ initialState, onRecoveryAttempt })
      )

      // Wait for initial effect
      await waitFor(() => {
        expect(result.current.lastKnownGoodState).toEqual(initialState)
      })

      act(() => {
        result.current.updateState({ step: 2 })
      })

      act(() => {
        result.current.attemptRecovery()
      })

      expect(onRecoveryAttempt).toHaveBeenCalledTimes(1)
    })

    it('does not call onRecoveryAttempt when lastKnownGoodState is null', () => {
      const onRecoveryAttempt = vi.fn()

      // With null initialState, lastKnownGoodState will be null initially
      // and even after effect runs, it will be set to null
      const { result } = renderHook(() =>
        useDiscoveryRecovery({ initialState: null, onRecoveryAttempt })
      )

      // Don't wait for effect - test immediate behavior
      let recovered: boolean
      act(() => {
        recovered = result.current.attemptRecovery()
      })

      // When lastKnownGoodState is null, recovery should fail
      expect(recovered!).toBe(false)
      expect(onRecoveryAttempt).not.toHaveBeenCalled()
    })

    it('returns false when no lastKnownGoodState is available', () => {
      const { result } = renderHook(() =>
        useDiscoveryRecovery({ initialState: null })
      )

      let recovered: boolean
      act(() => {
        recovered = result.current.attemptRecovery()
      })

      expect(recovered!).toBe(false)
    })
  })

  describe('reset', () => {
    it('resets currentState to initialState', () => {
      const initialState = { step: 1 }
      const newState = { step: 5 }

      const { result } = renderHook(() =>
        useDiscoveryRecovery({ initialState })
      )

      act(() => {
        result.current.updateState(newState)
      })

      expect(result.current.currentState).toEqual(newState)

      act(() => {
        result.current.reset()
      })

      expect(result.current.currentState).toEqual(initialState)
    })

    it('resets lastKnownGoodState to initialState', async () => {
      const initialState = { step: 1 }

      const { result } = renderHook(() =>
        useDiscoveryRecovery({ initialState })
      )

      // Wait for initial effects
      await waitFor(() => {
        expect(result.current.lastKnownGoodState).toEqual(initialState)
      })

      act(() => {
        result.current.updateState({ step: 2 })
        result.current.updateState({ step: 3 })
      })

      act(() => {
        result.current.reset()
      })

      expect(result.current.lastKnownGoodState).toEqual(initialState)
    })

    it('can be called multiple times', () => {
      const initialState = { value: 'initial' }

      const { result } = renderHook(() =>
        useDiscoveryRecovery({ initialState })
      )

      act(() => {
        result.current.updateState({ value: 'changed' })
        result.current.reset()
        result.current.updateState({ value: 'changed again' })
        result.current.reset()
      })

      expect(result.current.currentState).toEqual(initialState)
      expect(result.current.lastKnownGoodState).toEqual(initialState)
    })
  })

  describe('canRecover', () => {
    it('is true after initial effect runs with non-null initial state', async () => {
      const { result } = renderHook(() =>
        useDiscoveryRecovery({ initialState: { data: 'test' } })
      )

      await waitFor(() => {
        expect(result.current.canRecover).toBe(true)
      })
    })

    it('is false when initialState is null', async () => {
      const { result } = renderHook(() =>
        useDiscoveryRecovery({ initialState: null })
      )

      // Even after effect runs, canRecover should be false because
      // lastKnownGoodState will be set to null
      await waitFor(() => {
        expect(result.current.lastKnownGoodState).toBe(null)
      })

      expect(result.current.canRecover).toBe(false)
    })

    it('remains true after state updates', async () => {
      const { result } = renderHook(() =>
        useDiscoveryRecovery({ initialState: { step: 1 } })
      )

      await waitFor(() => {
        expect(result.current.canRecover).toBe(true)
      })

      act(() => {
        result.current.updateState({ step: 2 })
        result.current.updateState({ step: 3 })
      })

      expect(result.current.canRecover).toBe(true)
    })
  })

  describe('edge cases', () => {
    it('handles undefined values in state', () => {
      const initialState = { value: undefined as string | undefined }

      const { result } = renderHook(() =>
        useDiscoveryRecovery({ initialState })
      )

      act(() => {
        result.current.updateState({ value: 'defined' })
      })

      expect(result.current.currentState).toEqual({ value: 'defined' })

      act(() => {
        result.current.updateState({ value: undefined })
      })

      expect(result.current.currentState).toEqual({ value: undefined })
    })

    it('handles nested objects', async () => {
      const initialState = {
        user: { name: 'John', settings: { theme: 'dark' } },
      }

      const { result } = renderHook(() =>
        useDiscoveryRecovery({ initialState })
      )

      // Wait for effect
      await waitFor(() => {
        expect(result.current.lastKnownGoodState).toEqual(initialState)
      })

      const newState = {
        user: { name: 'Jane', settings: { theme: 'light' } },
      }

      act(() => {
        result.current.updateState(newState)
      })

      expect(result.current.currentState).toEqual(newState)
      expect(result.current.lastKnownGoodState).toEqual(initialState)
    })

    it('handles empty objects', async () => {
      const { result } = renderHook(() =>
        useDiscoveryRecovery({ initialState: {} })
      )

      await waitFor(() => {
        expect(result.current.lastKnownGoodState).toEqual({})
      })

      expect(result.current.currentState).toEqual({})
      expect(result.current.canRecover).toBe(true)
    })

    it('handles changing initialState prop', () => {
      const { result, rerender } = renderHook(
        ({ initialState }) => useDiscoveryRecovery({ initialState }),
        { initialProps: { initialState: { value: 'first' } } }
      )

      expect(result.current.currentState).toEqual({ value: 'first' })

      // Note: changing initialState doesn't change currentState
      // because useState only uses initialState on first render
      rerender({ initialState: { value: 'second' } })

      // currentState should still be 'first' because useState
      // ignores subsequent initialState changes
      expect(result.current.currentState).toEqual({ value: 'first' })
    })

    it('updateState function reference is stable', () => {
      const { result, rerender } = renderHook(() =>
        useDiscoveryRecovery({ initialState: { value: 'test' } })
      )

      const firstUpdateState = result.current.updateState

      rerender()

      expect(result.current.updateState).toBe(firstUpdateState)
    })

    it('works with complex workflow: update -> checkpoint -> update -> recover', async () => {
      const onRecoveryAttempt = vi.fn()
      const initialState = { stage: 'start', data: [] as string[] }

      const { result } = renderHook(() =>
        useDiscoveryRecovery({ initialState, onRecoveryAttempt })
      )

      // Wait for initial effect
      await waitFor(() => {
        expect(result.current.lastKnownGoodState).toEqual(initialState)
      })

      // Update to stage 1
      act(() => {
        result.current.updateState({ stage: 'stage1', data: ['item1'] })
      })

      // Save checkpoint at stage 1
      act(() => {
        result.current.saveCheckpoint()
      })

      // Update to stage 2
      act(() => {
        result.current.updateState({ stage: 'stage2', data: ['item1', 'item2'] })
      })

      // Something goes wrong at stage 2, recover
      act(() => {
        result.current.attemptRecovery()
      })

      // Should be back at stage 1 checkpoint
      expect(result.current.currentState).toEqual({ stage: 'stage1', data: ['item1'] })
      expect(onRecoveryAttempt).toHaveBeenCalledTimes(1)
    })
  })
})
