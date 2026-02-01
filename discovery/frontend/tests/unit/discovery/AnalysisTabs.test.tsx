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

  it('shows empty state with dimension name when no results', () => {
    render(<AnalysisTabs results={{ ROLE: [] }} activeDimension="ROLE" onDimensionChange={vi.fn()} />)
    expect(screen.getByText(/no results found for role/i)).toBeInTheDocument()
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

  describe('keyboard navigation', () => {
    it('navigates to next tab with ArrowRight', () => {
      const onDimensionChange = vi.fn()
      render(<AnalysisTabs results={results} activeDimension="ROLE" onDimensionChange={onDimensionChange} />)

      const roleTab = screen.getByRole('tab', { name: /role/i })
      fireEvent.keyDown(roleTab, { key: 'ArrowRight' })

      expect(onDimensionChange).toHaveBeenCalledWith('DEPARTMENT')
    })

    it('navigates to previous tab with ArrowLeft', () => {
      const onDimensionChange = vi.fn()
      render(<AnalysisTabs results={results} activeDimension="DEPARTMENT" onDimensionChange={onDimensionChange} />)

      const departmentTab = screen.getByRole('tab', { name: /department/i })
      fireEvent.keyDown(departmentTab, { key: 'ArrowLeft' })

      expect(onDimensionChange).toHaveBeenCalledWith('ROLE')
    })

    it('wraps around from last to first tab with ArrowRight', () => {
      const onDimensionChange = vi.fn()
      render(<AnalysisTabs results={results} activeDimension="DEPARTMENT" onDimensionChange={onDimensionChange} />)

      const departmentTab = screen.getByRole('tab', { name: /department/i })
      fireEvent.keyDown(departmentTab, { key: 'ArrowRight' })

      expect(onDimensionChange).toHaveBeenCalledWith('ROLE')
    })

    it('wraps around from first to last tab with ArrowLeft', () => {
      const onDimensionChange = vi.fn()
      render(<AnalysisTabs results={results} activeDimension="ROLE" onDimensionChange={onDimensionChange} />)

      const roleTab = screen.getByRole('tab', { name: /role/i })
      fireEvent.keyDown(roleTab, { key: 'ArrowLeft' })

      expect(onDimensionChange).toHaveBeenCalledWith('DEPARTMENT')
    })
  })

  describe('ARIA attributes', () => {
    it('has correct tab id attributes', () => {
      render(<AnalysisTabs results={results} activeDimension="ROLE" onDimensionChange={vi.fn()} />)

      expect(screen.getByRole('tab', { name: /role/i })).toHaveAttribute('id', 'tab-ROLE')
      expect(screen.getByRole('tab', { name: /department/i })).toHaveAttribute('id', 'tab-DEPARTMENT')
    })

    it('has correct tabIndex for active and inactive tabs', () => {
      render(<AnalysisTabs results={results} activeDimension="ROLE" onDimensionChange={vi.fn()} />)

      expect(screen.getByRole('tab', { name: /role/i })).toHaveAttribute('tabIndex', '0')
      expect(screen.getByRole('tab', { name: /department/i })).toHaveAttribute('tabIndex', '-1')
    })

    it('has matching aria-controls and tabpanel id', () => {
      render(<AnalysisTabs results={results} activeDimension="ROLE" onDimensionChange={vi.fn()} />)

      const roleTab = screen.getByRole('tab', { name: /role/i })
      expect(roleTab).toHaveAttribute('aria-controls', 'tabpanel-ROLE')

      const tabpanel = screen.getByRole('tabpanel')
      expect(tabpanel).toHaveAttribute('id', 'tabpanel-ROLE')
      expect(tabpanel).toHaveAttribute('aria-labelledby', 'tab-ROLE')
    })
  })
})
