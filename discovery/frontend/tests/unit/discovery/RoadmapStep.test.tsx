import { screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeEach } from 'vitest'
import { RoadmapStep } from '@/pages/discovery/RoadmapStep'
import { renderWithRouter } from '../../test-utils'
import { mockRoadmapApi, mockHandoffApi, resetAllMocks } from '../../__mocks__/services'

describe('RoadmapStep', () => {
  beforeEach(() => {
    resetAllMocks()
    // Set up mock roadmap items
    mockRoadmapApi.get.mockResolvedValue({
      items: [
        {
          id: 'roadmap-1',
          role_name: 'Software Engineer',
          priority_score: 0.92,
          priority_tier: 'HIGH',
          phase: 'NOW',
          estimated_effort: 'medium',
          order: 1,
        },
        {
          id: 'roadmap-2',
          role_name: 'Data Analyst',
          priority_score: 0.78,
          priority_tier: 'HIGH',
          phase: 'NEXT',
          estimated_effort: 'low',
          order: 2,
        },
        {
          id: 'roadmap-3',
          role_name: 'Customer Support',
          priority_score: 0.45,
          priority_tier: 'MEDIUM',
          phase: 'LATER',
          estimated_effort: 'high',
          order: 3,
        },
      ],
    })
  })

  it('shows loading state initially', async () => {
    renderWithRouter(<RoadmapStep />, {
      route: '/discovery/session-1/roadmap',
      routePath: '/discovery/:sessionId/roadmap',
    })

    // Should show loading initially
    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('renders kanban columns for phases', async () => {
    renderWithRouter(<RoadmapStep />, {
      route: '/discovery/session-1/roadmap',
      routePath: '/discovery/:sessionId/roadmap',
    })

    await waitFor(() => {
      // Component shows "Now", "Next", "Later" (not all caps)
      expect(screen.getByText('Now')).toBeInTheDocument()
      expect(screen.getByText('Next')).toBeInTheDocument()
      expect(screen.getByText('Later')).toBeInTheDocument()
    })
  })

  it('shows candidates in appropriate columns', async () => {
    renderWithRouter(<RoadmapStep />, {
      route: '/discovery/session-1/roadmap',
      routePath: '/discovery/:sessionId/roadmap',
    })

    await waitFor(() => {
      expect(screen.getByText(/software engineer/i)).toBeInTheDocument()
    })
  })

  it('allows dragging candidates between phases', async () => {
    renderWithRouter(<RoadmapStep />, {
      route: '/discovery/session-1/roadmap',
      routePath: '/discovery/:sessionId/roadmap',
    })

    const card = await screen.findByText(/software engineer/i)
    const draggableElement = card.closest('[draggable]')
    expect(draggableElement).toHaveAttribute('draggable', 'true')
  })

  it('shows candidate scores on cards', async () => {
    renderWithRouter(<RoadmapStep />, {
      route: '/discovery/session-1/roadmap',
      routePath: '/discovery/:sessionId/roadmap',
    })

    await waitFor(() => {
      // Look for priority label
      expect(screen.getAllByText(/priority/i).length).toBeGreaterThan(0)
    })
  })

  it('shows handoff button', async () => {
    renderWithRouter(<RoadmapStep />, {
      route: '/discovery/session-1/roadmap',
      routePath: '/discovery/:sessionId/roadmap',
    })

    await waitFor(() => {
      // Component uses "Hand off to Build" button
      expect(screen.getByRole('button', { name: /hand off/i })).toBeInTheDocument()
    })
  })

  it('opens handoff modal when button clicked', async () => {
    mockHandoffApi.validate.mockResolvedValueOnce({
      is_ready: true,
      warnings: [],
      errors: [],
    })

    renderWithRouter(<RoadmapStep />, {
      route: '/discovery/session-1/roadmap',
      routePath: '/discovery/:sessionId/roadmap',
    })

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /hand off/i })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /hand off/i }))

    await waitFor(() => {
      // Modal shows "Confirm Handoff" button
      expect(screen.getByText(/confirm handoff/i)).toBeInTheDocument()
    })
  })
})
