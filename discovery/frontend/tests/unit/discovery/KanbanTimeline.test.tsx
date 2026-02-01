import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { KanbanTimeline } from '@/components/features/discovery/KanbanTimeline'

const items = [
  { id: '1', name: 'Data Analyst', phase: 'NOW', priorityScore: 0.92 },
  { id: '2', name: 'Engineer', phase: 'NEXT', priorityScore: 0.78 },
  { id: '3', name: 'Manager', phase: 'LATER', priorityScore: 0.55 },
]

describe('KanbanTimeline', () => {
  it('renders three phase columns', () => {
    render(<KanbanTimeline items={items} onPhaseChange={vi.fn()} />)
    expect(screen.getByTestId('column-NOW')).toBeInTheDocument()
    expect(screen.getByTestId('column-NEXT')).toBeInTheDocument()
    expect(screen.getByTestId('column-LATER')).toBeInTheDocument()
  })

  it('places items in correct columns', () => {
    render(<KanbanTimeline items={items} onPhaseChange={vi.fn()} />)
    const nowColumn = screen.getByTestId('column-NOW')
    expect(nowColumn).toHaveTextContent('Data Analyst')
  })

  it('shows column counts', () => {
    render(<KanbanTimeline items={items} onPhaseChange={vi.fn()} />)
    expect(screen.getByText('NOW (1)')).toBeInTheDocument()
  })

  it('makes cards draggable', () => {
    render(<KanbanTimeline items={items} onPhaseChange={vi.fn()} />)
    const card = screen.getByText('Data Analyst').closest('[draggable]')
    expect(card).toHaveAttribute('draggable', 'true')
  })

  it('calls onPhaseChange when dropped', () => {
    const onPhaseChange = vi.fn()
    render(<KanbanTimeline items={items} onPhaseChange={onPhaseChange} />)
    const card = screen.getByText('Data Analyst')
    const nextColumn = screen.getByTestId('column-NEXT')
    fireEvent.dragStart(card)
    fireEvent.drop(nextColumn)
    expect(onPhaseChange).toHaveBeenCalledWith('1', 'NEXT')
  })

  it('shows drop zone highlight on drag over', () => {
    render(<KanbanTimeline items={items} onPhaseChange={vi.fn()} />)
    const nextColumn = screen.getByTestId('column-NEXT')
    fireEvent.dragEnter(nextColumn)
    expect(nextColumn).toHaveClass('ring-2')
  })

  it('renders empty column placeholder', () => {
    const singleItem = [{ id: '1', name: 'Test', phase: 'NOW', priorityScore: 0.9 }]
    render(<KanbanTimeline items={singleItem} onPhaseChange={vi.fn()} />)
    const laterColumn = screen.getByTestId('column-LATER')
    expect(laterColumn).toHaveTextContent(/drag items here/i)
  })
})
