// tests/unit/discovery/DwaAccordion.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { DwaAccordion } from '@/components/features/discovery/DwaAccordion'

const gwaGroup = {
  gwaId: '4.A.2.a.4',
  gwaTitle: 'Analyzing Data or Information',
  aiExposureScore: 0.72,
  dwas: [
    { id: '1', dwaId: '4.A.2.a.4.01', title: 'Analyze business data', isSelected: false },
    { id: '2', dwaId: '4.A.2.a.4.02', title: 'Interpret statistical results', isSelected: true },
  ],
}

describe('DwaAccordion', () => {
  it('renders GWA header with title', () => {
    render(<DwaAccordion group={gwaGroup} onDwaToggle={vi.fn()} />)
    expect(screen.getByText('Analyzing Data or Information')).toBeInTheDocument()
  })

  it('shows AI exposure score badge', () => {
    render(<DwaAccordion group={gwaGroup} onDwaToggle={vi.fn()} />)
    expect(screen.getByText('72%')).toBeInTheDocument()
  })

  it('expands to show DWAs on click', () => {
    render(<DwaAccordion group={gwaGroup} onDwaToggle={vi.fn()} />)
    const header = screen.getByRole('button')
    fireEvent.click(header)
    expect(screen.getByText('Analyze business data')).toBeVisible()
    expect(screen.getByText('Interpret statistical results')).toBeVisible()
  })

  it('shows selection state for each DWA', () => {
    render(<DwaAccordion group={gwaGroup} onDwaToggle={vi.fn()} defaultOpen={true} />)
    const selectedCheckbox = screen.getByRole('checkbox', { name: /interpret statistical/i })
    expect(selectedCheckbox).toBeChecked()
  })

  it('calls onDwaToggle when checkbox clicked', () => {
    const onDwaToggle = vi.fn()
    render(<DwaAccordion group={gwaGroup} onDwaToggle={onDwaToggle} defaultOpen={true} />)
    const checkbox = screen.getByRole('checkbox', { name: /analyze business/i })
    fireEvent.click(checkbox)
    expect(onDwaToggle).toHaveBeenCalledWith('1', true)
  })

  it('shows selection count in header', () => {
    render(<DwaAccordion group={gwaGroup} onDwaToggle={vi.fn()} />)
    expect(screen.getByText('1/2 selected')).toBeInTheDocument()
  })

  it('allows select all within group', () => {
    const onDwaToggle = vi.fn()
    render(<DwaAccordion group={gwaGroup} onDwaToggle={onDwaToggle} defaultOpen={true} />)
    const selectAllButton = screen.getByRole('button', { name: /select all/i })
    fireEvent.click(selectAllButton)
    expect(onDwaToggle).toHaveBeenCalledTimes(1)  // Unselected DWA
  })
})
