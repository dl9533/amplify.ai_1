import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { AnalysisTabs, AnalysisResults } from '@/components/features/discovery/AnalysisTabs'

const results: AnalysisResults = {
  ROLE: [
    { id: '1', name: 'Engineer', exposureScore: 0.72, impactScore: 0.85, priorityTier: 'HIGH' },
  ],
  DEPARTMENT: [
    { id: '2', name: 'Engineering', exposureScore: 0.68, impactScore: 0.75, priorityTier: 'MEDIUM' },
  ],
}

describe('AnalysisTabs', () => {
  it('renders tabs for each dimension', () => {
    render(<AnalysisTabs results={results} onDimensionChange={vi.fn()} />)
    expect(screen.getByRole('tab', { name: /role/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /department/i })).toBeInTheDocument()
  })

  it('shows result count in tab', () => {
    render(<AnalysisTabs results={results} onDimensionChange={vi.fn()} />)
    expect(screen.getByText(/role \(1\)/i)).toBeInTheDocument()
  })

  it('renders results for active tab', () => {
    render(<AnalysisTabs results={results} activeDimension="ROLE" onDimensionChange={vi.fn()} />)
    expect(screen.getByText('Engineer')).toBeInTheDocument()
  })

  it('calls onDimensionChange when tab clicked', () => {
    const onDimensionChange = vi.fn()
    render(<AnalysisTabs results={results} onDimensionChange={onDimensionChange} />)
    fireEvent.click(screen.getByRole('tab', { name: /department/i }))
    expect(onDimensionChange).toHaveBeenCalledWith('DEPARTMENT')
  })

  it('shows empty state when no results', () => {
    render(<AnalysisTabs results={{ ROLE: [] }} activeDimension="ROLE" onDimensionChange={vi.fn()} />)
    expect(screen.getByText(/no results/i)).toBeInTheDocument()
  })

  it('sorts results by priority by default', () => {
    const multipleResults: AnalysisResults = {
      ROLE: [
        { id: '1', name: 'Low', priorityTier: 'LOW', priorityScore: 0.3 },
        { id: '2', name: 'High', priorityTier: 'HIGH', priorityScore: 0.9 },
      ],
    }
    render(<AnalysisTabs results={multipleResults} activeDimension="ROLE" onDimensionChange={vi.fn()} />)
    const items = screen.getAllByTestId('analysis-result-card')
    expect(items[0]).toHaveTextContent('High')
  })
})
