import React, { useRef, useEffect, useState } from 'react'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
}

export interface QuickAction {
  label: string
  action: string
}

export interface ChatPanelProps {
  sessionId: string
  initialMessages?: ChatMessage[]
  onSendMessage?: (message: string) => void
  isLoading?: boolean
  quickActions?: QuickAction[]
}

export function ChatPanel({
  sessionId,
  initialMessages = [],
  onSendMessage,
  isLoading = false,
  quickActions = [],
}: ChatPanelProps): React.ReactElement {
  const [inputValue, setInputValue] = useState('')
  const scrollRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [initialMessages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (inputValue.trim() && onSendMessage) {
      onSendMessage(inputValue.trim())
      setInputValue('')
    }
  }

  const handleQuickAction = (action: QuickAction) => {
    if (onSendMessage) {
      onSendMessage(action.action)
    }
  }

  return (
    <section
      role="complementary"
      aria-label="Discovery chat"
      className="flex flex-col h-full"
      data-session-id={sessionId}
    >
      {/* Message List */}
      <div
        ref={scrollRef}
        role="log"
        aria-live="polite"
        className="flex-1 overflow-y-auto space-y-3 p-3"
      >
        {initialMessages.map((message) => (
          <div
            key={message.id}
            className={`
              p-3 rounded-lg text-sm
              ${message.role === 'user'
                ? 'bg-blue-100 text-blue-900 ml-6'
                : 'bg-gray-100 text-gray-900 mr-6'}
            `}
          >
            {message.content}
          </div>
        ))}

        {/* Loading Indicator */}
        {isLoading && (
          <div
            role="status"
            aria-label="Loading response"
            className="flex items-center gap-2 p-3 text-sm text-gray-500"
          >
            <span className="animate-pulse" style={{ animationDelay: '0ms' }}>●</span>
            <span className="animate-pulse" style={{ animationDelay: '150ms' }}>●</span>
            <span className="animate-pulse" style={{ animationDelay: '300ms' }}>●</span>
            <span className="sr-only">Loading...</span>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      {quickActions.length > 0 && (
        <div className="flex flex-wrap gap-2 px-3 py-2 border-t border-gray-200">
          {quickActions.map((action) => (
            <button
              key={action.action}
              type="button"
              onClick={() => handleQuickAction(action)}
              aria-label={`Quick action: ${action.label}`}
              className="px-3 py-1 text-xs font-medium text-blue-700 bg-blue-50 rounded-full hover:bg-blue-100 transition-colors"
            >
              {action.label}
            </button>
          ))}
        </div>
      )}

      {/* Input Form */}
      <form
        onSubmit={handleSubmit}
        className="flex gap-2 p-3 border-t border-gray-200"
      >
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          aria-label="Type a message"
          placeholder="Type a message..."
          className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={isLoading}
        />
        <button
          type="submit"
          aria-label="Send message"
          disabled={isLoading || !inputValue.trim()}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Send
        </button>
      </form>
    </section>
  )
}
