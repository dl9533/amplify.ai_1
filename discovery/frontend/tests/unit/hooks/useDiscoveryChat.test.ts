import { renderHook, act, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useDiscoveryChat } from '@/hooks/useDiscoveryChat'
import { mockChatApi, resetAllMocks } from '../../__mocks__/services'

describe('useDiscoveryChat', () => {
  const mockSessionId = 'test-session-123'

  beforeEach(() => {
    resetAllMocks()
    // Default mock for getHistory to return empty array
    mockChatApi.getHistory.mockResolvedValue([])
  })

  describe('initial state', () => {
    it('starts with empty messages when no initial messages provided', async () => {
      const { result } = renderHook(() =>
        useDiscoveryChat({ sessionId: mockSessionId })
      )

      // Wait for loadHistory to complete
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.messages).toEqual([])
      expect(result.current.error).toBeNull()
    })

    it('starts with provided initial messages', async () => {
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
      mockChatApi.sendMessage.mockResolvedValueOnce({
        response: 'Hello! How can I help you today?',
        quick_actions: [],
      })

      // Use non-empty initialMessages to prevent auto-loading
      const { result } = renderHook(() =>
        useDiscoveryChat({
          sessionId: mockSessionId,
          initialMessages: [{ id: 'init', role: 'assistant', content: 'Welcome!' }],
        })
      )

      await act(async () => {
        await result.current.sendMessage('Hello')
      })

      // Should have added user message (after initial)
      expect(result.current.messages).toHaveLength(3)
      expect(result.current.messages[1].role).toBe('user')
      expect(result.current.messages[1].content).toBe('Hello')

      // Should have added assistant response
      expect(result.current.messages[2].role).toBe('assistant')
      expect(result.current.messages[2].content).toBe('Hello! How can I help you today?')

      // Verify API was called correctly
      expect(mockChatApi.sendMessage).toHaveBeenCalledWith(mockSessionId, 'Hello')
    })

    it('does not send empty messages', async () => {
      const { result } = renderHook(() =>
        useDiscoveryChat({
          sessionId: mockSessionId,
          initialMessages: [{ id: 'init', role: 'assistant', content: 'Welcome!' }],
        })
      )

      await act(async () => {
        await result.current.sendMessage('')
        await result.current.sendMessage('   ')
      })

      // Still only the initial message
      expect(result.current.messages).toHaveLength(1)
      expect(mockChatApi.sendMessage).not.toHaveBeenCalled()
    })

    it('trims whitespace from messages', async () => {
      mockChatApi.sendMessage.mockResolvedValueOnce({
        response: 'Response',
        quick_actions: [],
      })

      const { result } = renderHook(() =>
        useDiscoveryChat({
          sessionId: mockSessionId,
          initialMessages: [{ id: 'init', role: 'assistant', content: 'Welcome!' }],
        })
      )

      await act(async () => {
        await result.current.sendMessage('  Hello world  ')
      })

      expect(result.current.messages[1].content).toBe('Hello world')
      expect(mockChatApi.sendMessage).toHaveBeenCalledWith(mockSessionId, 'Hello world')
    })
  })

  describe('loading state', () => {
    it('sets isLoading to true during API call', async () => {
      let resolvePromise: (value: unknown) => void
      const pendingPromise = new Promise((resolve) => {
        resolvePromise = resolve
      })

      mockChatApi.sendMessage.mockReturnValueOnce(
        pendingPromise as Promise<{ response: string; quick_actions: [] }>
      )

      const { result } = renderHook(() =>
        useDiscoveryChat({
          sessionId: mockSessionId,
          initialMessages: [{ id: 'init', role: 'assistant', content: 'Welcome!' }],
        })
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
          response: 'Response',
          quick_actions: [],
        })
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })
    })

    it('sets isLoading to false after successful response', async () => {
      mockChatApi.sendMessage.mockResolvedValueOnce({
        response: 'Response',
        quick_actions: [],
      })

      const { result } = renderHook(() =>
        useDiscoveryChat({
          sessionId: mockSessionId,
          initialMessages: [{ id: 'init', role: 'assistant', content: 'Welcome!' }],
        })
      )

      await act(async () => {
        await result.current.sendMessage('Hello')
      })

      expect(result.current.isLoading).toBe(false)
    })

    it('sets isLoading to false after error', async () => {
      mockChatApi.sendMessage.mockRejectedValueOnce(new Error('Network error'))

      const { result } = renderHook(() =>
        useDiscoveryChat({
          sessionId: mockSessionId,
          initialMessages: [{ id: 'init', role: 'assistant', content: 'Welcome!' }],
        })
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
      mockChatApi.sendMessage.mockRejectedValueOnce(networkError)

      const { result } = renderHook(() =>
        useDiscoveryChat({
          sessionId: mockSessionId,
          initialMessages: [{ id: 'init', role: 'assistant', content: 'Welcome!' }],
        })
      )

      await act(async () => {
        await result.current.sendMessage('Hello')
      })

      expect(result.current.error).toEqual(networkError)
    })

    it('sets error when API throws ApiError', async () => {
      const apiError = { message: 'Server error', name: 'ApiError' }
      mockChatApi.sendMessage.mockRejectedValueOnce(apiError)

      const { result } = renderHook(() =>
        useDiscoveryChat({
          sessionId: mockSessionId,
          initialMessages: [{ id: 'init', role: 'assistant', content: 'Welcome!' }],
        })
      )

      await act(async () => {
        await result.current.sendMessage('Hello')
      })

      expect(result.current.error).toBeInstanceOf(Error)
    })

    it('calls onError callback when error occurs', async () => {
      const onError = vi.fn()
      mockChatApi.sendMessage.mockRejectedValueOnce(new Error('Network error'))

      const { result } = renderHook(() =>
        useDiscoveryChat({
          sessionId: mockSessionId,
          initialMessages: [{ id: 'init', role: 'assistant', content: 'Welcome!' }],
          onError,
        })
      )

      await act(async () => {
        await result.current.sendMessage('Hello')
      })

      expect(onError).toHaveBeenCalledWith(expect.any(Error))
    })

    it('clears error on next successful send', async () => {
      mockChatApi.sendMessage
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          response: 'Response',
          quick_actions: [],
        })

      const { result } = renderHook(() =>
        useDiscoveryChat({
          sessionId: mockSessionId,
          initialMessages: [{ id: 'init', role: 'assistant', content: 'Welcome!' }],
        })
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
      mockChatApi.sendMessage.mockRejectedValueOnce('String error')

      const { result } = renderHook(() =>
        useDiscoveryChat({
          sessionId: mockSessionId,
          initialMessages: [{ id: 'init', role: 'assistant', content: 'Welcome!' }],
        })
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
      mockChatApi.sendMessage.mockRejectedValueOnce(new Error('Network error'))

      const { result } = renderHook(() =>
        useDiscoveryChat({
          sessionId: mockSessionId,
          initialMessages: [{ id: 'init', role: 'assistant', content: 'Welcome!' }],
        })
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
        useDiscoveryChat({
          sessionId: mockSessionId,
          initialMessages: [{ id: 'init', role: 'assistant', content: 'Welcome!' }],
        })
      )

      act(() => {
        result.current.addMessage({
          id: 'custom-1',
          role: 'assistant',
          content: 'System message',
        })
      })

      expect(result.current.messages).toHaveLength(2)
      expect(result.current.messages[1]).toEqual({
        id: 'custom-1',
        role: 'assistant',
        content: 'System message',
      })
    })

    it('appends messages in order', () => {
      const { result } = renderHook(() =>
        useDiscoveryChat({
          sessionId: mockSessionId,
          initialMessages: [{ id: 'init', role: 'assistant', content: 'Welcome!' }],
        })
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

      expect(result.current.messages).toHaveLength(3)
      expect(result.current.messages[1].content).toBe('First')
      expect(result.current.messages[2].content).toBe('Second')
    })
  })
})
