import { useState, useCallback } from 'react'
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

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim()) return

      setError(null)

      // Add user message immediately
      const userMessage: ChatMessage = {
        id: generateMessageId(),
        role: 'user',
        content: content.trim(),
      }
      addMessage(userMessage)

      setIsLoading(true)

      try {
        // API call to send message and get response
        const response = await fetch(`/api/discovery/sessions/${sessionId}/messages`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ content: content.trim() }),
        })

        if (!response.ok) {
          throw new Error(`Failed to send message: ${response.statusText}`)
        }

        const data = await response.json()

        // Add assistant response
        const assistantMessage: ChatMessage = {
          id: data.id || generateMessageId(),
          role: 'assistant',
          content: data.content,
        }
        addMessage(assistantMessage)
      } catch (err) {
        const errorObj = err instanceof Error ? err : new Error('Failed to send message')
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
  }
}
