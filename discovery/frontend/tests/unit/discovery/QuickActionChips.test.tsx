import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { QuickActionChips } from '@/components/features/discovery/QuickActionChips'

const chips = [
  { label: 'Confirm all', action: 'confirm_all', variant: 'primary' },
  { label: 'Skip step', action: 'skip', variant: 'secondary' },
  { label: 'Show help', action: 'help', variant: 'ghost' },
]

describe('QuickActionChips', () => {
  it('renders all chips', () => {
    render(<QuickActionChips chips={chips} onAction={vi.fn()} />)

    expect(screen.getByText('Confirm all')).toBeInTheDocument()
    expect(screen.getByText('Skip step')).toBeInTheDocument()
    expect(screen.getByText('Show help')).toBeInTheDocument()
  })

  it('calls onAction with correct action when clicked', () => {
    const onAction = vi.fn()
    render(<QuickActionChips chips={chips} onAction={onAction} />)

    fireEvent.click(screen.getByText('Confirm all'))

    expect(onAction).toHaveBeenCalledWith('confirm_all')
  })

  it('applies variant styling', () => {
    render(<QuickActionChips chips={chips} onAction={vi.fn()} />)

    const primaryChip = screen.getByText('Confirm all')
    expect(primaryChip).toHaveClass('bg-primary')
  })

  it('disables chips when loading', () => {
    render(<QuickActionChips chips={chips} onAction={vi.fn()} isLoading={true} />)

    const chip = screen.getByText('Confirm all')
    expect(chip).toBeDisabled()
  })

  it('handles empty chips array', () => {
    const { container } = render(<QuickActionChips chips={[]} onAction={vi.fn()} />)

    expect(container.firstChild).toBeEmptyDOMElement()
  })

  it('uses secondary variant by default', () => {
    const chips = [{ label: 'Default', action: 'default' }]
    render(<QuickActionChips chips={chips} onAction={vi.fn()} />)

    const button = screen.getByRole('button', { name: 'Default' })
    expect(button).toHaveClass('bg-background-muted')
  })

  it('has accessible button roles', () => {
    render(<QuickActionChips chips={chips} onAction={vi.fn()} />)

    const buttons = screen.getAllByRole('button')
    expect(buttons).toHaveLength(3)
  })
})
