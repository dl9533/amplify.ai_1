import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { AnalysisStep } from '@/pages/discovery/AnalysisStep'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

const renderWithRouter = (ui: React.ReactElement) => {
  return render(
    <MemoryRouter initialEntries={['/discovery/session-1/analysis']}>
      <Routes>
        <Route path="/discovery/:sessionId/analysis" element={ui} />
      </Routes>
    </MemoryRouter>
  )
}

describe('AnalysisStep', () => {
  it('renders dimension tabs', async () => {
    renderWithRouter(<AnalysisStep />)
    expect(screen.getByRole('tab', { name: /role/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /department/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /geography/i })).toBeInTheDocument()
  })

  it('shows analysis results for selected dimension', async () => {
    renderWithRouter(<AnalysisStep />)
    await waitFor(() => {
      expect(screen.getByText(/software engineer/i)).toBeInTheDocument()
    })
  })

  it('displays scores for each result', async () => {
    renderWithRouter(<AnalysisStep />)
    await waitFor(() => {
      expect(screen.getAllByText(/exposure:/i).length).toBeGreaterThan(0)
      expect(screen.getAllByText(/impact:/i).length).toBeGreaterThan(0)
      expect(screen.getAllByText(/priority:/i).length).toBeGreaterThan(0)
    })
  })

  it('shows priority tier badges', async () => {
    renderWithRouter(<AnalysisStep />)
    await waitFor(() => {
      expect(screen.getByText('HIGH')).toBeInTheDocument()
    })
  })

  it('switches dimension on tab click', async () => {
    renderWithRouter(<AnalysisStep />)
    fireEvent.click(screen.getByRole('tab', { name: /department/i }))
    await waitFor(() => {
      expect(screen.getByText(/engineering/i)).toBeInTheDocument()
    })
  })

  it('allows filtering by priority tier', async () => {
    renderWithRouter(<AnalysisStep />)
    await waitFor(() => {
      expect(screen.getByText(/software engineer/i)).toBeInTheDocument()
    })
    const filterSelect = screen.getByRole('combobox', { name: /filter/i })
    fireEvent.change(filterSelect, { target: { value: 'HIGH' } })
    // Results should be filtered - LOW tier results (Customer Support) should not appear
    await waitFor(() => {
      expect(screen.queryByText(/customer support/i)).not.toBeInTheDocument()
    })
  })

  it('shows loading state during analysis', () => {
    renderWithRouter(<AnalysisStep />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })
})
