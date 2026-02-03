import { screen, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeEach } from 'vitest'
import { ActivitiesStep } from '@/pages/discovery/ActivitiesStep'
import { renderWithRouter } from '../../test-utils'
import { mockActivitiesApi, resetAllMocks } from '../../__mocks__/services'

describe('ActivitiesStep', () => {
  beforeEach(() => {
    resetAllMocks()
    // Explicitly set up mock implementation
    mockActivitiesApi.getBySession.mockResolvedValue([
      {
        gwa_code: 'GWA-001',
        gwa_title: 'Analyzing Data',
        ai_exposure_score: 0.72,
        dwas: [
          {
            id: 'dwa-001',
            code: 'DWA-001',
            title: 'Analyze business data',
            description: 'Analyze business data to identify trends',
            selected: false,
            gwa_code: 'GWA-001',
          },
        ],
      },
    ])
  })

  it('shows loading state initially', async () => {
    renderWithRouter(<ActivitiesStep />, {
      route: '/discovery/session-1/activities',
      routePath: '/discovery/:sessionId/activities',
    })

    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('renders GWA groups after loading', async () => {
    renderWithRouter(<ActivitiesStep />, {
      route: '/discovery/session-1/activities',
      routePath: '/discovery/:sessionId/activities',
    })

    await waitFor(() => {
      expect(screen.getByText(/analyzing data/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('shows step title and description', async () => {
    renderWithRouter(<ActivitiesStep />, {
      route: '/discovery/session-1/activities',
      routePath: '/discovery/:sessionId/activities',
    })

    await waitFor(() => {
      expect(screen.getByText(/select work activities/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('shows selection count', async () => {
    renderWithRouter(<ActivitiesStep />, {
      route: '/discovery/session-1/activities',
      routePath: '/discovery/:sessionId/activities',
    })

    await waitFor(() => {
      expect(screen.getByText(/activities selected/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('has auto-select button for high exposure activities', async () => {
    renderWithRouter(<ActivitiesStep />, {
      route: '/discovery/session-1/activities',
      routePath: '/discovery/:sessionId/activities',
    })

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /auto-select high exposure/i })).toBeInTheDocument()
    }, { timeout: 3000 })
  })
})
