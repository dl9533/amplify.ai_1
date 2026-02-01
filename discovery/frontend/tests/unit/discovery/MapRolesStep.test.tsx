import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MapRolesStep } from '@/pages/discovery/MapRolesStep'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

const renderWithRouter = (ui: React.ReactElement) => {
  return render(
    <MemoryRouter initialEntries={['/discovery/session-1/map-roles']}>
      <Routes>
        <Route path="/discovery/:sessionId/map-roles" element={ui} />
      </Routes>
    </MemoryRouter>
  )
}

describe('MapRolesStep', () => {
  it('renders role mapping list', async () => {
    renderWithRouter(<MapRolesStep />)

    await waitFor(() => {
      expect(screen.getByText(/map your roles/i)).toBeInTheDocument()
    })
  })

  it('shows auto-detected mappings', async () => {
    renderWithRouter(<MapRolesStep />)

    await waitFor(() => {
      expect(screen.getByText(/software engineer/i)).toBeInTheDocument()
    })
  })

  it('allows confirming a mapping', async () => {
    renderWithRouter(<MapRolesStep />)

    const confirmButtons = await screen.findAllByRole('button', { name: /^confirm$/i })
    fireEvent.click(confirmButtons[0])

    await waitFor(() => {
      expect(screen.getByTestId('confirmed-badge')).toBeInTheDocument()
    })
  })

  it('allows bulk confirm above threshold', async () => {
    renderWithRouter(<MapRolesStep />)

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText(/software engineer/i)).toBeInTheDocument()
    })

    const bulkConfirmButton = screen.getByRole('button', { name: /confirm all above/i })
    expect(bulkConfirmButton).toBeInTheDocument()

    // Click bulk confirm (threshold 80%)
    fireEvent.click(bulkConfirmButton)

    // Verify mappings above 80% get confirmed (Software Engineer 95%, Data Analyst 87%)
    // Project Manager at 78% should NOT be confirmed
    await waitFor(() => {
      const confirmedBadges = screen.getAllByTestId('confirmed-badge')
      // Software Engineer (95%) and Data Analyst (87%) should be confirmed
      expect(confirmedBadges.length).toBe(2)
    })

    // Verify Project Manager (78%) still has a confirm button
    const remainingConfirmButtons = screen.getAllByRole('button', { name: /^confirm$/i })
    expect(remainingConfirmButtons.length).toBe(1)
  })

  it('shows confidence score for each mapping', async () => {
    renderWithRouter(<MapRolesStep />)

    await waitFor(() => {
      expect(screen.getByText(/95%/)).toBeInTheDocument()
    })
  })

  it('enables search to remap roles', async () => {
    renderWithRouter(<MapRolesStep />)

    await waitFor(() => {
      expect(screen.getByRole('combobox', { name: /search o\*net/i })).toBeInTheDocument()
    })
  })
})
