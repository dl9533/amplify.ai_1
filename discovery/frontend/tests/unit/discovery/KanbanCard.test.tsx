import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { KanbanCard, getPriorityColor } from '@/components/features/discovery/KanbanCard'

const baseItem = {
  id: '1',
  name: 'Data Analyst',
  phase: 'NOW' as const,
  priorityScore: 0.92,
}

describe('KanbanCard', () => {
  describe('rendering', () => {
    it('renders item name', () => {
      render(<KanbanCard item={baseItem} onDragStart={vi.fn()} />)
      expect(screen.getByText('Data Analyst')).toBeInTheDocument()
    })

    it('renders priority score as percentage', () => {
      render(<KanbanCard item={baseItem} onDragStart={vi.fn()} />)
      expect(screen.getByText('92% priority')).toBeInTheDocument()
    })

    it('renders with high priority score (>= 0.8)', () => {
      const item = { ...baseItem, priorityScore: 0.85 }
      render(<KanbanCard item={item} onDragStart={vi.fn()} />)
      expect(screen.getByText('85% priority')).toBeInTheDocument()
    })

    it('renders with medium priority score (>= 0.6)', () => {
      const item = { ...baseItem, priorityScore: 0.65 }
      render(<KanbanCard item={item} onDragStart={vi.fn()} />)
      expect(screen.getByText('65% priority')).toBeInTheDocument()
    })

    it('renders with low priority score (< 0.6)', () => {
      const item = { ...baseItem, priorityScore: 0.45 }
      render(<KanbanCard item={item} onDragStart={vi.fn()} />)
      expect(screen.getByText('45% priority')).toBeInTheDocument()
    })
  })

  describe('getPriorityColor utility', () => {
    it('returns green for high priority (>= 0.8)', () => {
      expect(getPriorityColor(0.8)).toBe('bg-green-100 text-green-800')
      expect(getPriorityColor(0.95)).toBe('bg-green-100 text-green-800')
      expect(getPriorityColor(1.0)).toBe('bg-green-100 text-green-800')
    })

    it('returns yellow for medium priority (>= 0.6, < 0.8)', () => {
      expect(getPriorityColor(0.6)).toBe('bg-yellow-100 text-yellow-800')
      expect(getPriorityColor(0.7)).toBe('bg-yellow-100 text-yellow-800')
      expect(getPriorityColor(0.79)).toBe('bg-yellow-100 text-yellow-800')
    })

    it('returns gray for low priority (< 0.6)', () => {
      expect(getPriorityColor(0.59)).toBe('bg-gray-100 text-gray-800')
      expect(getPriorityColor(0.3)).toBe('bg-gray-100 text-gray-800')
      expect(getPriorityColor(0)).toBe('bg-gray-100 text-gray-800')
    })
  })

  describe('accessibility attributes', () => {
    it('has role listitem', () => {
      render(<KanbanCard item={baseItem} onDragStart={vi.fn()} />)
      expect(screen.getByRole('listitem')).toBeInTheDocument()
    })

    it('has aria-label with name and priority', () => {
      render(<KanbanCard item={baseItem} onDragStart={vi.fn()} />)
      const card = screen.getByRole('listitem')
      expect(card).toHaveAttribute(
        'aria-label',
        expect.stringContaining('Data Analyst')
      )
      expect(card).toHaveAttribute('aria-label', expect.stringContaining('92%'))
    })

    it('is focusable with tabIndex', () => {
      render(<KanbanCard item={baseItem} onDragStart={vi.fn()} />)
      const card = screen.getByRole('listitem')
      expect(card).toHaveAttribute('tabIndex', '0')
    })

    it('has aria-grabbed attribute defaulting to false', () => {
      render(<KanbanCard item={baseItem} onDragStart={vi.fn()} />)
      const card = screen.getByRole('listitem')
      expect(card).toHaveAttribute('aria-grabbed', 'false')
    })

    it('has aria-grabbed true when isGrabbed is true', () => {
      render(<KanbanCard item={baseItem} onDragStart={vi.fn()} isGrabbed={true} />)
      const card = screen.getByRole('listitem')
      expect(card).toHaveAttribute('aria-grabbed', 'true')
    })
  })

  describe('drag and drop', () => {
    it('is draggable', () => {
      render(<KanbanCard item={baseItem} onDragStart={vi.fn()} />)
      const card = screen.getByRole('listitem')
      expect(card).toHaveAttribute('draggable', 'true')
    })

    it('calls onDragStart with item id when drag begins', () => {
      const onDragStart = vi.fn()
      render(<KanbanCard item={baseItem} onDragStart={onDragStart} />)
      const card = screen.getByRole('listitem')
      fireEvent.dragStart(card)
      expect(onDragStart).toHaveBeenCalledTimes(1)
      expect(onDragStart).toHaveBeenCalledWith(expect.any(Object), '1')
    })

    it('passes correct item id for different items', () => {
      const onDragStart = vi.fn()
      const item = { ...baseItem, id: 'test-id-123' }
      render(<KanbanCard item={item} onDragStart={onDragStart} />)
      const card = screen.getByRole('listitem')
      fireEvent.dragStart(card)
      expect(onDragStart).toHaveBeenCalledWith(expect.any(Object), 'test-id-123')
    })
  })

  describe('keyboard navigation', () => {
    it('calls onKeyboardMove with left direction on ArrowLeft', () => {
      const onKeyboardMove = vi.fn()
      render(
        <KanbanCard
          item={baseItem}
          onDragStart={vi.fn()}
          onKeyboardMove={onKeyboardMove}
        />
      )
      const card = screen.getByRole('listitem')
      fireEvent.keyDown(card, { key: 'ArrowLeft' })
      expect(onKeyboardMove).toHaveBeenCalledWith('1', 'left')
    })

    it('calls onKeyboardMove with right direction on ArrowRight', () => {
      const onKeyboardMove = vi.fn()
      render(
        <KanbanCard
          item={baseItem}
          onDragStart={vi.fn()}
          onKeyboardMove={onKeyboardMove}
        />
      )
      const card = screen.getByRole('listitem')
      fireEvent.keyDown(card, { key: 'ArrowRight' })
      expect(onKeyboardMove).toHaveBeenCalledWith('1', 'right')
    })

    it('does not call onKeyboardMove for other keys', () => {
      const onKeyboardMove = vi.fn()
      render(
        <KanbanCard
          item={baseItem}
          onDragStart={vi.fn()}
          onKeyboardMove={onKeyboardMove}
        />
      )
      const card = screen.getByRole('listitem')
      fireEvent.keyDown(card, { key: 'Enter' })
      fireEvent.keyDown(card, { key: 'Space' })
      fireEvent.keyDown(card, { key: 'ArrowUp' })
      fireEvent.keyDown(card, { key: 'ArrowDown' })
      expect(onKeyboardMove).not.toHaveBeenCalled()
    })

    it('handles keyboard events gracefully when onKeyboardMove is not provided', () => {
      render(<KanbanCard item={baseItem} onDragStart={vi.fn()} />)
      const card = screen.getByRole('listitem')
      // Should not throw
      expect(() => {
        fireEvent.keyDown(card, { key: 'ArrowLeft' })
        fireEvent.keyDown(card, { key: 'ArrowRight' })
      }).not.toThrow()
    })
  })
})
