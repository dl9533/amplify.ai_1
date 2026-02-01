import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ActivitiesStep } from '@/pages/discovery/ActivitiesStep'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

const renderWithRouter = (ui: React.ReactElement) => {
  return render(
    <MemoryRouter initialEntries={['/discovery/session-1/activities']}>
      <Routes>
        <Route path="/discovery/:sessionId/activities" element={ui} />
      </Routes>
    </MemoryRouter>
  )
}

describe('ActivitiesStep', () => {
  it('renders GWA groups', async () => {
    renderWithRouter(<ActivitiesStep />)

    await waitFor(() => {
      expect(screen.getByText(/analyzing data/i)).toBeInTheDocument()
    })
  })

  it('shows AI exposure score for each GWA', async () => {
    renderWithRouter(<ActivitiesStep />)

    await waitFor(() => {
      expect(screen.getByText(/72%/)).toBeInTheDocument()
    })
  })

  it('expands GWA to show DWAs', async () => {
    renderWithRouter(<ActivitiesStep />)

    const accordion = await screen.findByRole('button', { name: /analyzing data/i })
    fireEvent.click(accordion)

    await waitFor(() => {
      expect(screen.getByText(/analyze business data/i)).toBeInTheDocument()
    })
  })

  it('allows selecting individual DWAs', async () => {
    renderWithRouter(<ActivitiesStep />)

    const accordion = await screen.findByRole('button', { name: /analyzing data/i })
    fireEvent.click(accordion)

    const checkbox = await screen.findByRole('checkbox', { name: /analyze business data/i })
    fireEvent.click(checkbox)

    expect(checkbox).toBeChecked()
  })

  it('shows selection count', async () => {
    renderWithRouter(<ActivitiesStep />)

    await waitFor(() => {
      expect(screen.getByText(/0 activities selected/i)).toBeInTheDocument()
    })
  })

  it('enables bulk select for high exposure activities', async () => {
    renderWithRouter(<ActivitiesStep />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /select high exposure/i })).toBeInTheDocument()
    })
  })
})
