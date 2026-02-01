import { renderHook, act, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useDiscoveryChat } from '@/hooks/useDiscoveryChat'

describe('useDiscoveryChat', () => {
  const mockSessionId = 'test-session-123'

  beforeEach(() => {
    vi.resetAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('initial state', () => {
    it('starts with empty messages when no initial messages provided', () => {
      const { result } = renderHook(() =>
        useDiscoveryChat({ sessionId: mockSessionId })
      )

      expect(result.current.messages).toEqual([])
      expect(result.current.isLoading).toBe(false)
      expect(result.current.error).toBeNull()
    })

    it('starts with provided initial messages', () => {
      const initialMessages = [
        { id: '1', role: 'user' as const, content: 'Hello' },
        { id: '2', role: 'assistant' as const, content: 'Hi there!' },
      ]

      const { result } = renderHook(() =>
        useDiscoveryChat({ sessionId: mockSessionId, initialMessages })
      )

      expect(result.current.messages).toEqual(initialMessages)
      expect(result.current.isLoading).toBe(false)
    })
  })

  describe('sendMessage', () => {
    it('adds user message and calls API', async () => {
      const mockResponse = {
        id: 'assistant-msg-1',
        content: 'Hello! How can I help you today?',
      }

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })

      const { result } = renderHook(() =>
        useDiscoveryChat({ sessionId: mockSessionId })
      )

      await act(async () => {
        await result.current.sendMessage('Hello')
      })

      // Should have added user message
      expect(result.current.messages).toHaveLength(2)
      expect(result.current.messages[0].role).toBe('user')
      expect(result.current.messages[0].content).toBe('Hello')

      // Should have added assistant response
      expect(result.current.messages[1].role).toBe('assistant')
      expect(result.current.messages[1].content).toBe('Hello! How can I help you today?')

      // Verify fetch was called correctly
      expect(fetch).toHaveBeenCalledWith(
        `/api/discovery/sessions/${mockSessionId}/messages`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ content: 'Hello' }),
        }
      )
    })

    it('does not send empty messages', async () => {
      global.fetch = vi.fn()

      const { result } = renderHook(() =>
        useDiscoveryChat({ sessionId: mockSessionId })
      )

      await act(async () => {
        await result.current.sendMessage('')
        await result.current.sendMessage('   ')
      })

      expect(result.current.messages).toHaveLength(0)
      expect(fetch).not.toHaveBeenCalled()
    })

    it('trims whitespace from messages', async () => {
      const mockResponse = {
        id: 'assistant-msg-1',
        content: 'Response',
      }

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })

      const { result } = renderHook(() =>
        useDiscoveryChat({ sessionId: mockSessionId })
      )

      await act(async () => {
        await result.current.sendMessage('  Hello world  ')
      })

      expect(result.current.messages[0].content).toBe('Hello world')
      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          body: JSON.stringify({ content: 'Hello world' }),
        })
      )
    })
  })

  describe('loading state', () => {
    it('sets isLoading to true during API call', async () => {
      let resolvePromise: (value: unknown) => void
      const pendingPromise = new Promise((resolve) => {
        resolvePromise = resolve
      })

      global.fetch = vi.fn().mockReturnValueOnce(pendingPromise)

      const { result } = renderHook(() =>
        useDiscoveryChat({ sessionId: mockSessionId })
      )

      expect(result.current.isLoading).toBe(false)

      act(() => {
        result.current.sendMessage('Hello')
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(true)
      })

      // Resolve the promise
      await act(async () => {
        resolvePromise!({
          ok: true,
          json: () => Promise.resolve({ id: '1', content: 'Response' }),
        })
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })
    })

    it('sets isLoading to false after successful response', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: '1', content: 'Response' }),
      })

      const { result } = renderHook(() =>
        useDiscoveryChat({ sessionId: mockSessionId })
      )

      await act(async () => {
        await result.current.sendMessage('Hello')
      })

      expect(result.current.isLoading).toBe(false)
    })

    it('sets isLoading to false after error', async () => {
      global.fetch = vi.fn().mockRejectedValueOnce(new Error('Network error'))

      const { result } = renderHook(() =>
        useDiscoveryChat({ sessionId: mockSessionId })
      )

      await act(async () => {
        await result.current.sendMessage('Hello')
      })

      expect(result.current.isLoading).toBe(false)
    })
  })

  describe('error handling', () => {
    it('sets error when API call fails with network error', async () => {
      const networkError = new Error('Network error')
      global.fetch = vi.fn().mockRejectedValueOnce(networkError)

      const { result } = renderHook(() =>
        useDiscoveryChat({ sessionId: mockSessionId })
      )

      await act(async () => {
        await result.current.sendMessage('Hello')
      })

      expect(result.current.error).toEqual(networkError)
    })

    it('sets error when API returns non-ok response', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        statusText: 'Internal Server Error',
      })

      const { result } = renderHook(() =>
        useDiscoveryChat({ sessionId: mockSessionId })
      )

      await act(async () => {
        await result.current.sendMessage('Hello')
      })

      expect(result.current.error).toBeInstanceOf(Error)
      expect(result.current.error?.message).toContain('Failed to send message')
      expect(result.current.error?.message).toContain('Internal Server Error')
    })

    it('calls onError callback when error occurs', async () => {
      const onError = vi.fn()
      global.fetch = vi.fn().mockRejectedValueOnce(new Error('Network error'))

      const { result } = renderHook(() =>
        useDiscoveryChat({ sessionId: mockSessionId, onError })
      )

      await act(async () => {
        await result.current.sendMessage('Hello')
      })

      expect(onError).toHaveBeenCalledWith(expect.any(Error))
    })

    it('clears error on next successful send', async () => {
      global.fetch = vi
        .fn()
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ id: '1', content: 'Response' }),
        })

      const { result } = renderHook(() =>
        useDiscoveryChat({ sessionId: mockSessionId })
      )

      // First call fails
      await act(async () => {
        await result.current.sendMessage('Hello')
      })
      expect(result.current.error).not.toBeNull()

      // Second call succeeds
      await act(async () => {
        await result.current.sendMessage('Hello again')
      })
      expect(result.current.error).toBeNull()
    })

    it('wraps non-Error exceptions in Error object', async () => {
      global.fetch = vi.fn().mockRejectedValueOnce('String error')

      const { result } = renderHook(() =>
        useDiscoveryChat({ sessionId: mockSessionId })
      )

      await act(async () => {
        await result.current.sendMessage('Hello')
      })

      expect(result.current.error).toBeInstanceOf(Error)
      expect(result.current.error?.message).toBe('Failed to send message')
    })
  })

  describe('clearMessages', () => {
    it('clears all messages', async () => {
      const initialMessages = [
        { id: '1', role: 'user' as const, content: 'Hello' },
        { id: '2', role: 'assistant' as const, content: 'Hi!' },
      ]

      const { result } = renderHook(() =>
        useDiscoveryChat({ sessionId: mockSessionId, initialMessages })
      )

      expect(result.current.messages).toHaveLength(2)

      act(() => {
        result.current.clearMessages()
      })

      expect(result.current.messages).toHaveLength(0)
    })

    it('clears error when clearing messages', async () => {
      global.fetch = vi.fn().mockRejectedValueOnce(new Error('Network error'))

      const { result } = renderHook(() =>
        useDiscoveryChat({ sessionId: mockSessionId })
      )

      await act(async () => {
        await result.current.sendMessage('Hello')
      })
      expect(result.current.error).not.toBeNull()

      act(() => {
        result.current.clearMessages()
      })

      expect(result.current.error).toBeNull()
    })
  })

  describe('addMessage', () => {
    it('adds a message to the list', () => {
      const { result } = renderHook(() =>
        useDiscoveryChat({ sessionId: mockSessionId })
      )

      act(() => {
        result.current.addMessage({
          id: 'custom-1',
          role: 'assistant',
          content: 'System message',
        })
      })

      expect(result.current.messages).toHaveLength(1)
      expect(result.current.messages[0]).toEqual({
        id: 'custom-1',
        role: 'assistant',
        content: 'System message',
      })
    })

    it('appends messages in order', () => {
      const { result } = renderHook(() =>
        useDiscoveryChat({ sessionId: mockSessionId })
      )

      act(() => {
        result.current.addMessage({
          id: '1',
          role: 'user',
          content: 'First',
        })
      })

      act(() => {
        result.current.addMessage({
          id: '2',
          role: 'assistant',
          content: 'Second',
        })
      })

      expect(result.current.messages).toHaveLength(2)
      expect(result.current.messages[0].content).toBe('First')
      expect(result.current.messages[1].content).toBe('Second')
    })
  })
})
