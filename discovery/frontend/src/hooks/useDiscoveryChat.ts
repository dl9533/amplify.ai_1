import { useState, useCallback, useEffect } from 'react'
import { chatApi, ApiError } from '../services'
import type { ChatMessage } from '../components/features/discovery/ChatPanel'

export interface UseDiscoveryChatOptions {
  sessionId: string
  initialMessages?: ChatMessage[]
  onError?: (error: Error) => void
}

export interface UseDiscoveryChatReturn {
  messages: ChatMessage[]
  isLoading: boolean
  error: Error | null
  sendMessage: (content: string) => Promise<void>
  clearMessages: () => void
  addMessage: (message: ChatMessage) => void
  loadHistory: () => Promise<void>
}

let messageIdCounter = 0

function generateMessageId(): string {
  messageIdCounter += 1
  return `msg-${Date.now()}-${messageIdCounter}`
}

export function useDiscoveryChat({
  sessionId,
  initialMessages = [],
  onError,
}: UseDiscoveryChatOptions): UseDiscoveryChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const addMessage = useCallback((message: ChatMessage) => {
    setMessages((prev) => [...prev, message])
  }, [])

  const loadHistory = useCallback(async () => {
    if (!sessionId) return

    try {
      setIsLoading(true)
      setError(null)

      const history = await chatApi.getHistory(sessionId)

      // Map API response to ChatMessage format
      const loadedMessages: ChatMessage[] = history.map((item) => ({
        id: generateMessageId(),
        role: item.role,
        content: item.content,
      }))

      setMessages(loadedMessages)
    } catch (err) {
      const errorObj =
        err instanceof ApiError
          ? new Error(err.message)
          : err instanceof Error
            ? err
            : new Error('Failed to load chat history')
      setError(errorObj)
      onError?.(errorObj)
    } finally {
      setIsLoading(false)
    }
  }, [sessionId, onError])

  // Load history on mount if no initial messages
  useEffect(() => {
    if (initialMessages.length === 0 && sessionId) {
      loadHistory()
    }
  }, [sessionId, initialMessages.length, loadHistory])

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim()) return

      setError(null)

      // Add user message immediately (optimistic update)
      const userMessage: ChatMessage = {
        id: generateMessageId(),
        role: 'user',
        content: content.trim(),
      }
      addMessage(userMessage)

      setIsLoading(true)

      try {
        const response = await chatApi.sendMessage(sessionId, content.trim())

        // Add assistant response
        const assistantMessage: ChatMessage = {
          id: generateMessageId(),
          role: 'assistant',
          content: response.response,
        }
        addMessage(assistantMessage)
      } catch (err) {
        const errorObj =
          err instanceof ApiError
            ? new Error(err.message)
            : err instanceof Error
              ? err
              : new Error('Failed to send message')
        setError(errorObj)
        onError?.(errorObj)
      } finally {
        setIsLoading(false)
      }
    },
    [sessionId, addMessage, onError]
  )

  const clearMessages = useCallback(() => {
    setMessages([])
    setError(null)
  }, [])

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearMessages,
    addMessage,
    loadHistory,
  }
}
