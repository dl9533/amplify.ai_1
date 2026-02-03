import { screen, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeEach } from 'vitest'
import { AnalysisStep } from '@/pages/discovery/AnalysisStep'
import { renderWithRouter } from '../../test-utils'
import { mockAnalysisApi, resetAllMocks } from '../../__mocks__/services'

describe('AnalysisStep', () => {
  beforeEach(() => {
    resetAllMocks()
    // Explicitly set up mock implementation
    mockAnalysisApi.getByDimension.mockResolvedValue({
      dimension: 'ROLE',
      results: [
        {
          id: 'result-1',
          name: 'Software Engineer',
          ai_exposure_score: 0.85,
          impact_score: 0.72,
          complexity_score: 0.3,
          priority_score: 0.78,
          priority_tier: 'HIGH',
        },
      ],
    })
  })

  it('renders dimension tabs', async () => {
    renderWithRouter(<AnalysisStep />, {
      route: '/discovery/session-1/analysis',
      routePath: '/discovery/:sessionId/analysis',
    })

    await waitFor(() => {
      expect(screen.getByText('By Role')).toBeInTheDocument()
      expect(screen.getByText('By Department')).toBeInTheDocument()
      expect(screen.getByText('By Geography')).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('shows analysis results for selected dimension', async () => {
    renderWithRouter(<AnalysisStep />, {
      route: '/discovery/session-1/analysis',
      routePath: '/discovery/:sessionId/analysis',
    })

    await waitFor(() => {
      expect(screen.getByText(/software engineer/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('shows step title', async () => {
    renderWithRouter(<AnalysisStep />, {
      route: '/discovery/session-1/analysis',
      routePath: '/discovery/:sessionId/analysis',
    })

    await waitFor(() => {
      expect(screen.getByText(/analysis results/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('shows table structure when results load', async () => {
    renderWithRouter(<AnalysisStep />, {
      route: '/discovery/session-1/analysis',
      routePath: '/discovery/:sessionId/analysis',
    })

    // Wait for results to load
    await waitFor(() => {
      expect(screen.getByText(/software engineer/i)).toBeInTheDocument()
    }, { timeout: 3000 })

    // Check that table is rendered (look for table element or common header text)
    const tables = document.querySelectorAll('table')
    expect(tables.length).toBeGreaterThan(0)
  })
})
