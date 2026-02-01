import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { RoadmapStep } from '@/pages/discovery/RoadmapStep'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

const renderWithRouter = (ui: React.ReactElement) => {
  return render(
    <MemoryRouter initialEntries={['/discovery/session-1/roadmap']}>
      <Routes>
        <Route path="/discovery/:sessionId/roadmap" element={ui} />
      </Routes>
    </MemoryRouter>
  )
}

describe('RoadmapStep', () => {
  it('renders kanban columns for phases', async () => {
    renderWithRouter(<RoadmapStep />)
    await waitFor(() => {
      expect(screen.getByText('NOW')).toBeInTheDocument()
      expect(screen.getByText('NEXT')).toBeInTheDocument()
      expect(screen.getByText('LATER')).toBeInTheDocument()
    })
  })

  it('shows candidates in appropriate columns', async () => {
    renderWithRouter(<RoadmapStep />)
    await waitFor(() => {
      expect(screen.getByText(/software engineer/i)).toBeInTheDocument()
    })
  })

  it('allows dragging candidates between phases', async () => {
    renderWithRouter(<RoadmapStep />)
    const card = await screen.findByText(/software engineer/i)
    expect(card.closest('[draggable]')).toHaveAttribute('draggable', 'true')
  })

  it('shows candidate scores on cards', async () => {
    renderWithRouter(<RoadmapStep />)
    await waitFor(() => {
      expect(screen.getByText(/priority: 0.92/i)).toBeInTheDocument()
    })
  })

  it('enables export options', () => {
    renderWithRouter(<RoadmapStep />)
    expect(screen.getByRole('button', { name: /export/i })).toBeInTheDocument()
  })

  it('shows handoff button', () => {
    renderWithRouter(<RoadmapStep />)
    expect(screen.getByRole('button', { name: /send to intake/i })).toBeInTheDocument()
  })

  it('validates before handoff', async () => {
    renderWithRouter(<RoadmapStep />)
    fireEvent.click(screen.getByRole('button', { name: /send to intake/i }))
    await waitFor(() => {
      expect(screen.getByText(/confirm handoff/i)).toBeInTheDocument()
    })
  })
})
