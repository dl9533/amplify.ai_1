import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, Mock } from 'vitest'
import { DiscoverySessionList } from '@/pages/discovery/DiscoverySessionList'
import { MemoryRouter } from 'react-router-dom'
import * as useDiscoverySessionsModule from '@/hooks/useDiscoverySessions'

// Mock the hook
vi.mock('@/hooks/useDiscoverySessions', () => ({
  useDiscoverySessions: vi.fn(),
}))

const mockSessions: useDiscoverySessionsModule.DiscoverySession[] = [
  {
    id: 'session-1',
    name: 'Q1 Discovery',
    status: 'In Progress',
    currentStep: 2,
    totalSteps: 5,
    createdAt: '2026-01-15T10:00:00Z',
    updatedAt: '2026-01-20T14:30:00Z',
  },
  {
    id: 'session-2',
    name: 'Engineering Team Analysis',
    status: 'Completed',
    currentStep: 5,
    totalSteps: 5,
    createdAt: '2025-12-01T09:00:00Z',
    updatedAt: '2025-12-15T16:45:00Z',
  },
  {
    id: 'session-3',
    name: 'HR Department Discovery',
    status: 'Draft',
    currentStep: 1,
    totalSteps: 5,
    createdAt: '2026-01-25T11:00:00Z',
    updatedAt: '2026-01-25T11:00:00Z',
  },
]

const defaultMockReturn: useDiscoverySessionsModule.UseDiscoverySessionsReturn = {
  sessions: mockSessions,
  isLoading: false,
  error: null,
  page: 1,
  totalPages: 1,
  setPage: vi.fn(),
  createSession: vi.fn().mockResolvedValue(mockSessions[0]),
  deleteSession: vi.fn().mockResolvedValue(undefined),
  isCreating: false,
  isDeleting: null,
}

describe('DiscoverySessionList', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    ;(useDiscoverySessionsModule.useDiscoverySessions as Mock).mockReturnValue(defaultMockReturn)
  })

  it('renders list of sessions', async () => {
    render(<MemoryRouter><DiscoverySessionList /></MemoryRouter>)
    await waitFor(() => {
      expect(screen.getByText(/q1 discovery/i)).toBeInTheDocument()
    })
  })

  it('shows session status', async () => {
    render(<MemoryRouter><DiscoverySessionList /></MemoryRouter>)
    await waitFor(() => {
      expect(screen.getByText('In Progress')).toBeInTheDocument()
    })
  })

  it('shows current step for each session', async () => {
    render(<MemoryRouter><DiscoverySessionList /></MemoryRouter>)
    await waitFor(() => {
      expect(screen.getByText(/step 2 of 5/i)).toBeInTheDocument()
    })
  })

  it('allows creating new session', async () => {
    render(<MemoryRouter><DiscoverySessionList /></MemoryRouter>)
    const createButton = screen.getByRole('button', { name: /new discovery/i })
    expect(createButton).toBeInTheDocument()
  })

  it('allows deleting a session', async () => {
    render(<MemoryRouter><DiscoverySessionList /></MemoryRouter>)
    const deleteButtons = await screen.findAllByRole('button', { name: /delete/i })
    fireEvent.click(deleteButtons[0])
    await waitFor(() => {
      expect(screen.getByText(/confirm delete/i)).toBeInTheDocument()
    })
  })

  it('links to continue session', async () => {
    render(<MemoryRouter><DiscoverySessionList /></MemoryRouter>)
    const continueLinks = await screen.findAllByRole('link', { name: /continue/i })
    expect(continueLinks[0]).toHaveAttribute('href', expect.stringContaining('/discovery/'))
  })

  it('shows empty state when no sessions', async () => {
    ;(useDiscoverySessionsModule.useDiscoverySessions as Mock).mockReturnValue({
      ...defaultMockReturn,
      sessions: [],
    })

    render(<MemoryRouter><DiscoverySessionList /></MemoryRouter>)

    await waitFor(() => {
      expect(screen.getByText(/no sessions found/i)).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: /start your first discovery/i })).toBeInTheDocument()
  })

  it('supports pagination', async () => {
    render(<MemoryRouter><DiscoverySessionList /></MemoryRouter>)
    await waitFor(() => {
      expect(screen.getByRole('navigation', { name: /pagination/i })).toBeInTheDocument()
    })
  })

  it('shows loading state', async () => {
    ;(useDiscoverySessionsModule.useDiscoverySessions as Mock).mockReturnValue({
      ...defaultMockReturn,
      sessions: [],
      isLoading: true,
    })

    render(<MemoryRouter><DiscoverySessionList /></MemoryRouter>)

    expect(screen.getByText(/loading sessions/i)).toBeInTheDocument()
  })

  it('shows error state', async () => {
    ;(useDiscoverySessionsModule.useDiscoverySessions as Mock).mockReturnValue({
      ...defaultMockReturn,
      sessions: [],
      error: 'Failed to load sessions',
    })

    render(<MemoryRouter><DiscoverySessionList /></MemoryRouter>)

    expect(screen.getByRole('alert')).toBeInTheDocument()
    expect(screen.getByText(/an error occurred/i)).toBeInTheDocument()
  })

  it('calls createSession when clicking New Discovery button', async () => {
    const mockCreateSession = vi.fn().mockResolvedValue(mockSessions[0])
    ;(useDiscoverySessionsModule.useDiscoverySessions as Mock).mockReturnValue({
      ...defaultMockReturn,
      createSession: mockCreateSession,
    })

    render(<MemoryRouter><DiscoverySessionList /></MemoryRouter>)

    const createButton = screen.getByRole('button', { name: /new discovery/i })
    fireEvent.click(createButton)

    await waitFor(() => {
      expect(mockCreateSession).toHaveBeenCalled()
    })
  })

  it('calls deleteSession after confirming delete', async () => {
    const mockDeleteSession = vi.fn().mockResolvedValue(undefined)
    ;(useDiscoverySessionsModule.useDiscoverySessions as Mock).mockReturnValue({
      ...defaultMockReturn,
      deleteSession: mockDeleteSession,
    })

    render(<MemoryRouter><DiscoverySessionList /></MemoryRouter>)

    // Click delete on first session
    const deleteButtons = await screen.findAllByRole('button', { name: /delete q1 discovery/i })
    fireEvent.click(deleteButtons[0])

    // Confirm delete
    await waitFor(() => {
      expect(screen.getByText(/confirm delete/i)).toBeInTheDocument()
    })

    const confirmButton = screen.getByRole('button', { name: /confirm delete/i })
    fireEvent.click(confirmButton)

    await waitFor(() => {
      expect(mockDeleteSession).toHaveBeenCalledWith('session-1')
    })
  })

  it('closes modal when canceling delete', async () => {
    render(<MemoryRouter><DiscoverySessionList /></MemoryRouter>)

    // Click delete on first session
    const deleteButtons = await screen.findAllByRole('button', { name: /delete q1 discovery/i })
    fireEvent.click(deleteButtons[0])

    // Modal should be open
    await waitFor(() => {
      expect(screen.getByText(/confirm delete/i)).toBeInTheDocument()
    })

    // Click cancel
    const cancelButton = screen.getByRole('button', { name: /cancel delete/i })
    fireEvent.click(cancelButton)

    // Modal should be closed
    await waitFor(() => {
      expect(screen.queryByText(/confirm delete/i)).not.toBeInTheDocument()
    })
  })
})
