import { useState, useRef, useEffect, FormEvent } from 'react'
import { useParams } from 'react-router-dom'
import { IconSend, IconSpinner, IconX, IconZap } from '../../ui/Icons'
import { useDiscoveryChat } from '../../../hooks/useDiscoveryChat'

interface ChatPanelProps {
  onClose?: () => void
}

export function ChatPanel({ onClose }: ChatPanelProps) {
  const { sessionId } = useParams()
  const {
    messages,
    isLoading,
    sendMessage,
  } = useDiscoveryChat(sessionId || '')

  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    const trimmedInput = input.trim()
    if (!trimmedInput || isLoading) return

    setInput('')
    await sendMessage(trimmedInput)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  // Quick action suggestions
  const quickActions = [
    { label: 'High exposure roles', action: 'Which roles have the highest AI exposure?' },
    { label: 'Best candidates', action: 'What are the best automation candidates?' },
    { label: 'Next steps', action: 'What should I focus on next?' },
  ]

  const handleQuickAction = (action: string) => {
    sendMessage(action)
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="shrink-0 px-4 py-3 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-accent/15 flex items-center justify-center">
            <IconZap size={16} className="text-accent" />
          </div>
          <div>
            <h3 className="text-sm font-semibold font-display text-default">
              Discovery Assistant
            </h3>
            <p className="text-xs text-muted">AI-powered guidance</p>
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="btn-ghost p-1.5 rounded-md"
            aria-label="Close chat"
          >
            <IconX size={18} className="text-muted" />
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-12 h-12 rounded-full bg-accent/10 flex items-center justify-center mx-auto mb-3">
              <IconZap size={20} className="text-accent" />
            </div>
            <h4 className="text-sm font-medium text-default mb-1">
              How can I help?
            </h4>
            <p className="text-xs text-muted mb-4">
              Ask questions about your workforce data or get guidance on next steps.
            </p>

            {/* Quick actions */}
            <div className="space-y-2">
              {quickActions.map((qa, index) => (
                <button
                  key={index}
                  onClick={() => handleQuickAction(qa.action)}
                  className="w-full text-left px-3 py-2 text-sm text-muted bg-bg-muted rounded-lg hover:bg-bg-subtle hover:text-default transition-colors"
                >
                  {qa.label}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`
                  max-w-[85%] px-3 py-2 rounded-xl text-sm
                  ${
                    message.role === 'user'
                      ? 'bg-accent text-white rounded-br-sm'
                      : 'bg-bg-muted text-default rounded-bl-sm'
                  }
                `}
              >
                <p className="whitespace-pre-wrap">{message.content}</p>
              </div>
            </div>
          ))
        )}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-bg-muted px-4 py-3 rounded-xl rounded-bl-sm">
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-muted animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-1.5 h-1.5 rounded-full bg-muted animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-1.5 h-1.5 rounded-full bg-muted animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="shrink-0 p-4 border-t border-border">
        <form onSubmit={handleSubmit} className="relative">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question..."
            rows={1}
            className="
              w-full px-4 py-3 pr-12 text-sm
              bg-bg-muted text-default placeholder:text-subtle
              border border-border rounded-xl
              resize-none
              focus:border-accent focus:ring-1 focus:ring-accent/30
              transition-all
            "
            style={{
              minHeight: '48px',
              maxHeight: '120px',
            }}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="
              absolute right-2 bottom-2
              w-8 h-8 rounded-lg
              bg-accent text-white
              flex items-center justify-center
              disabled:opacity-30 disabled:cursor-not-allowed
              hover:brightness-110 transition-all
            "
          >
            {isLoading ? (
              <IconSpinner size={16} />
            ) : (
              <IconSend size={16} />
            )}
          </button>
        </form>
        <p className="text-xs text-faint text-center mt-2">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  )
}

// Export the type for the message
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp?: Date
}
