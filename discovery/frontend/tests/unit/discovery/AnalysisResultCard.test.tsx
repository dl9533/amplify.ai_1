import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { AnalysisResultCard, AnalysisResult } from '@/components/features/discovery/AnalysisResultCard'

describe('AnalysisResultCard', () => {
  it('renders with all score types', () => {
    const result: AnalysisResult = {
      id: '1',
      name: 'Test Result',
      exposureScore: 0.75,
      impactScore: 0.85,
      priorityTier: 'HIGH',
      priorityScore: 0.9,
    }

    render(<AnalysisResultCard result={result} />)

    expect(screen.getByText('Test Result')).toBeInTheDocument()
    expect(screen.getByText('75%')).toBeInTheDocument()
    expect(screen.getByText('85%')).toBeInTheDocument()
    expect(screen.getByText('HIGH')).toBeInTheDocument()
  })

  it('renders without optional scores', () => {
    const result: AnalysisResult = {
      id: '2',
      name: 'Minimal Result',
      priorityTier: 'LOW',
    }

    render(<AnalysisResultCard result={result} />)

    expect(screen.getByText('Minimal Result')).toBeInTheDocument()
    expect(screen.getByText('LOW')).toBeInTheDocument()
    expect(screen.queryByText('Exposure Score')).not.toBeInTheDocument()
    expect(screen.queryByText('Impact Score')).not.toBeInTheDocument()
  })

  it('renders with only exposure score', () => {
    const result: AnalysisResult = {
      id: '3',
      name: 'Exposure Only',
      exposureScore: 0.5,
      priorityTier: 'MEDIUM',
    }

    render(<AnalysisResultCard result={result} />)

    expect(screen.getByText('Exposure Score')).toBeInTheDocument()
    expect(screen.getByText('50%')).toBeInTheDocument()
    expect(screen.queryByText('Impact Score')).not.toBeInTheDocument()
  })

  it('renders with only impact score', () => {
    const result: AnalysisResult = {
      id: '4',
      name: 'Impact Only',
      impactScore: 0.65,
      priorityTier: 'MEDIUM',
    }

    render(<AnalysisResultCard result={result} />)

    expect(screen.getByText('Impact Score')).toBeInTheDocument()
    expect(screen.getByText('65%')).toBeInTheDocument()
    expect(screen.queryByText('Exposure Score')).not.toBeInTheDocument()
  })

  describe('badge color mapping', () => {
    it('displays red badge for HIGH priority', () => {
      const result: AnalysisResult = {
        id: '5',
        name: 'High Priority',
        priorityTier: 'HIGH',
      }

      render(<AnalysisResultCard result={result} />)

      const badge = screen.getByText('HIGH')
      expect(badge).toHaveClass('bg-red-100', 'text-red-800')
    })

    it('displays yellow badge for MEDIUM priority', () => {
      const result: AnalysisResult = {
        id: '6',
        name: 'Medium Priority',
        priorityTier: 'MEDIUM',
      }

      render(<AnalysisResultCard result={result} />)

      const badge = screen.getByText('MEDIUM')
      expect(badge).toHaveClass('bg-yellow-100', 'text-yellow-800')
    })

    it('displays green badge for LOW priority', () => {
      const result: AnalysisResult = {
        id: '7',
        name: 'Low Priority',
        priorityTier: 'LOW',
      }

      render(<AnalysisResultCard result={result} />)

      const badge = screen.getByText('LOW')
      expect(badge).toHaveClass('bg-green-100', 'text-green-800')
    })
  })

  it('has data-testid attribute', () => {
    const result: AnalysisResult = {
      id: '8',
      name: 'Testable Result',
      priorityTier: 'MEDIUM',
    }

    render(<AnalysisResultCard result={result} />)

    expect(screen.getByTestId('analysis-result-card')).toBeInTheDocument()
  })
})
