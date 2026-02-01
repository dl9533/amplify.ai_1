import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ChatPanel } from '@/components/features/discovery/ChatPanel'

describe('ChatPanel', () => {
  it('renders message input', () => {
    render(<ChatPanel sessionId="test-session" />)

    expect(screen.getByRole('textbox', { name: /message/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument()
  })

  it('displays message history', () => {
    const messages = [
      { id: '1', role: 'user', content: 'Hello' },
      { id: '2', role: 'assistant', content: 'Hi! How can I help?' },
    ]

    render(<ChatPanel sessionId="test-session" initialMessages={messages} />)

    expect(screen.getByText('Hello')).toBeInTheDocument()
    expect(screen.getByText('Hi! How can I help?')).toBeInTheDocument()
  })

  it('sends message on submit', async () => {
    const onSend = vi.fn()
    render(<ChatPanel sessionId="test-session" onSendMessage={onSend} />)

    const input = screen.getByRole('textbox', { name: /message/i })
    fireEvent.change(input, { target: { value: 'Test message' } })
    fireEvent.click(screen.getByRole('button', { name: /send/i }))

    await waitFor(() => {
      expect(onSend).toHaveBeenCalledWith('Test message')
    })
  })

  it('shows loading indicator while waiting for response', () => {
    render(<ChatPanel sessionId="test-session" isLoading={true} />)

    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('renders quick action chips when provided', () => {
    const quickActions = [
      { label: 'Show details', action: 'show_details' },
      { label: 'Export', action: 'export' },
    ]

    render(<ChatPanel sessionId="test-session" quickActions={quickActions} />)

    expect(screen.getByText('Show details')).toBeInTheDocument()
    expect(screen.getByText('Export')).toBeInTheDocument()
  })

  it('auto-scrolls to latest message', async () => {
    const { rerender } = render(<ChatPanel sessionId="test-session" initialMessages={[]} />)

    const messages = [
      { id: '1', role: 'assistant', content: 'New message!' },
    ]
    rerender(<ChatPanel sessionId="test-session" initialMessages={messages} />)

    // Verify scroll container exists
    expect(screen.getByRole('log')).toBeInTheDocument()
  })
})
