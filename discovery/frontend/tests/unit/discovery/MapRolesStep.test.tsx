import { screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeEach } from 'vitest'
import { MapRolesStep } from '@/pages/discovery/MapRolesStep'
import { renderWithRouter } from '../../test-utils'
import { mockRoleMappingsApi, resetAllMocks } from '../../__mocks__/services'

describe('MapRolesStep', () => {
  beforeEach(() => {
    resetAllMocks()
    // Explicitly set up the mock implementation
    mockRoleMappingsApi.getBySession.mockResolvedValue([
      {
        id: 'mapping-1',
        source_role: 'Software Developer',
        onet_code: '15-1252.00',
        onet_title: 'Software Developers',
        confidence_score: 0.92,
        is_confirmed: false,
      },
      {
        id: 'mapping-2',
        source_role: 'Data Scientist',
        onet_code: '15-2051.00',
        onet_title: 'Data Scientists',
        confidence_score: 0.88,
        is_confirmed: true,
      },
    ])
  })

  it('shows loading state initially', async () => {
    renderWithRouter(<MapRolesStep />, {
      route: '/discovery/session-1/map-roles',
      routePath: '/discovery/:sessionId/map-roles',
    })

    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('renders role mapping list', async () => {
    renderWithRouter(<MapRolesStep />, {
      route: '/discovery/session-1/map-roles',
      routePath: '/discovery/:sessionId/map-roles',
    })

    await waitFor(() => {
      expect(screen.getByText(/map roles to o\*net/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('shows auto-detected mappings', async () => {
    renderWithRouter(<MapRolesStep />, {
      route: '/discovery/session-1/map-roles',
      routePath: '/discovery/:sessionId/map-roles',
    })

    await waitFor(() => {
      const elements = screen.getAllByText(/software developer/i)
      expect(elements.length).toBeGreaterThan(0)
    }, { timeout: 3000 })
  })

  it('allows confirming a mapping', async () => {
    mockRoleMappingsApi.update.mockResolvedValueOnce({
      id: 'mapping-1',
      source_role: 'Software Developer',
      onet_code: '15-1252.00',
      onet_title: 'Software Developers',
      confidence_score: 0.92,
      is_confirmed: true,
    })

    renderWithRouter(<MapRolesStep />, {
      route: '/discovery/session-1/map-roles',
      routePath: '/discovery/:sessionId/map-roles',
    })

    await waitFor(() => {
      expect(screen.getAllByText(/software developer/i).length).toBeGreaterThan(0)
    }, { timeout: 3000 })

    const confirmButtons = screen.getAllByRole('button', { name: /confirm$/i })
    expect(confirmButtons.length).toBeGreaterThan(0)
    fireEvent.click(confirmButtons[0])

    await waitFor(() => {
      expect(mockRoleMappingsApi.update).toHaveBeenCalled()
    }, { timeout: 3000 })
  })

  it('allows bulk confirm above threshold', async () => {
    mockRoleMappingsApi.bulkConfirm.mockResolvedValueOnce({ confirmed_count: 2 })

    renderWithRouter(<MapRolesStep />, {
      route: '/discovery/session-1/map-roles',
      routePath: '/discovery/:sessionId/map-roles',
    })

    await waitFor(() => {
      expect(screen.getAllByText(/software developer/i).length).toBeGreaterThan(0)
    }, { timeout: 3000 })

    const bulkConfirmButton = screen.getByRole('button', { name: /confirm all/i })
    expect(bulkConfirmButton).toBeInTheDocument()

    fireEvent.click(bulkConfirmButton)

    await waitFor(() => {
      expect(mockRoleMappingsApi.bulkConfirm).toHaveBeenCalled()
    }, { timeout: 3000 })
  })

  it('has remap functionality', async () => {
    renderWithRouter(<MapRolesStep />, {
      route: '/discovery/session-1/map-roles',
      routePath: '/discovery/:sessionId/map-roles',
    })

    await waitFor(() => {
      expect(screen.getAllByText(/software developer/i).length).toBeGreaterThan(0)
    }, { timeout: 3000 })

    const remapButtons = screen.getAllByRole('button', { name: /remap/i })
    expect(remapButtons.length).toBeGreaterThan(0)
  })
})
