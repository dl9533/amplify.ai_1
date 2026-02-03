import { screen, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeEach } from 'vitest'
import { ChatPanel } from '@/components/features/discovery/ChatPanel'
import { renderWithRouter } from '../../test-utils'
import { mockChatApi, resetAllMocks } from '../../__mocks__/services'

describe('ChatPanel', () => {
  beforeEach(() => {
    resetAllMocks()
    // Set up mock to return empty history (will show quick actions)
    mockChatApi.getHistory.mockResolvedValue([])
    // Set up mock for sendMessage
    mockChatApi.sendMessage.mockResolvedValue({
      response: 'Hello! I can help you.',
      quick_actions: [],
    })
  })

  it('renders message input', async () => {
    renderWithRouter(<ChatPanel />, {
      route: '/discovery/session-1',
      routePath: '/discovery/:sessionId',
    })

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/ask a question/i)).toBeInTheDocument()
    })
  })

  it('displays quick action buttons when no messages', async () => {
    renderWithRouter(<ChatPanel />, {
      route: '/discovery/session-1',
      routePath: '/discovery/:sessionId',
    })

    // Wait for history to load (empty) so quick actions appear
    await waitFor(() => {
      expect(screen.getByText('High exposure roles')).toBeInTheDocument()
      expect(screen.getByText('Best candidates')).toBeInTheDocument()
      expect(screen.getByText('Next steps')).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('shows assistant title', async () => {
    renderWithRouter(<ChatPanel />, {
      route: '/discovery/session-1',
      routePath: '/discovery/:sessionId',
    })

    await waitFor(() => {
      expect(screen.getByText('Discovery Assistant')).toBeInTheDocument()
    })
  })

  it('shows close button when onClose is provided', async () => {
    const onClose = () => {}

    renderWithRouter(<ChatPanel onClose={onClose} />, {
      route: '/discovery/session-1',
      routePath: '/discovery/:sessionId',
    })

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /close chat/i })).toBeInTheDocument()
    })
  })

  it('has submit button', async () => {
    renderWithRouter(<ChatPanel />, {
      route: '/discovery/session-1',
      routePath: '/discovery/:sessionId',
    })

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '' })).toBeInTheDocument()
    })
  })
})
