import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { RoleMappingCard } from '@/components/features/discovery/RoleMappingCard'

const mapping = {
  id: '1',
  sourceRole: 'Software Engineer',
  onetCode: '15-1252.00',
  onetTitle: 'Software Developers',
  confidenceScore: 0.95,
  isConfirmed: false,
  headcount: 45,
}

describe('RoleMappingCard', () => {
  it('renders source role and O*NET mapping', () => {
    render(<RoleMappingCard mapping={mapping} onConfirm={vi.fn()} onRemap={vi.fn()} />)

    expect(screen.getByText('Software Engineer')).toBeInTheDocument()
    expect(screen.getByText('Software Developers')).toBeInTheDocument()
    expect(screen.getByText('15-1252.00')).toBeInTheDocument()
  })

  it('shows confidence score as percentage', () => {
    render(<RoleMappingCard mapping={mapping} onConfirm={vi.fn()} onRemap={vi.fn()} />)

    expect(screen.getByText('95%')).toBeInTheDocument()
  })

  it('shows headcount', () => {
    render(<RoleMappingCard mapping={mapping} onConfirm={vi.fn()} onRemap={vi.fn()} />)

    expect(screen.getByText('45 employees')).toBeInTheDocument()
  })

  it('calls onConfirm when confirm clicked', () => {
    const onConfirm = vi.fn()
    render(<RoleMappingCard mapping={mapping} onConfirm={onConfirm} onRemap={vi.fn()} />)

    fireEvent.click(screen.getByRole('button', { name: /confirm/i }))

    expect(onConfirm).toHaveBeenCalledWith(mapping.id)
  })

  it('calls onRemap when remap clicked', () => {
    const onRemap = vi.fn()
    render(<RoleMappingCard mapping={mapping} onConfirm={vi.fn()} onRemap={onRemap} />)

    fireEvent.click(screen.getByRole('button', { name: /remap/i }))

    expect(onRemap).toHaveBeenCalledWith(mapping.id)
  })

  it('shows confirmed state', () => {
    const confirmedMapping = { ...mapping, isConfirmed: true }
    render(<RoleMappingCard mapping={confirmedMapping} onConfirm={vi.fn()} onRemap={vi.fn()} />)

    expect(screen.getByTestId('confirmed-badge')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /confirm/i })).not.toBeInTheDocument()
  })

  it('shows low confidence warning', () => {
    const lowConfidenceMapping = { ...mapping, confidenceScore: 0.45 }
    render(<RoleMappingCard mapping={lowConfidenceMapping} onConfirm={vi.fn()} onRemap={vi.fn()} />)

    expect(screen.getByText(/low confidence/i)).toBeInTheDocument()
  })
})
