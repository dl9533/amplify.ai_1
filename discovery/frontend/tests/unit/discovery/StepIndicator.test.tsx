import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StepIndicator } from '@/components/features/discovery'
import type { Step } from '@/components/features/discovery'

const steps: Step[] = [
  { id: 1, title: 'Upload', status: 'completed' },
  { id: 2, title: 'Map Roles', status: 'current' },
  { id: 3, title: 'Activities', status: 'upcoming' },
  { id: 4, title: 'Analysis', status: 'upcoming' },
  { id: 5, title: 'Roadmap', status: 'upcoming' },
]

describe('StepIndicator', () => {
  it('renders all steps', () => {
    render(<StepIndicator steps={steps} currentStep={2} />)

    // Should render all step titles
    expect(screen.getByText('Upload')).toBeInTheDocument()
    expect(screen.getByText('Map Roles')).toBeInTheDocument()
    expect(screen.getByText('Activities')).toBeInTheDocument()
    expect(screen.getByText('Analysis')).toBeInTheDocument()
    expect(screen.getByText('Roadmap')).toBeInTheDocument()

    // Should render as a list
    const listItems = screen.getAllByRole('listitem')
    expect(listItems).toHaveLength(5)
  })

  it('marks completed steps with checkmark', () => {
    render(<StepIndicator steps={steps} currentStep={2} />)

    const listItems = screen.getAllByRole('listitem')
    const completedStep = listItems[0]

    // Completed step should have data-status="completed"
    expect(completedStep).toHaveAttribute('data-status', 'completed')

    // Should contain a checkmark
    expect(completedStep.textContent).toContain('✓')
  })

  it('highlights current step', () => {
    render(<StepIndicator steps={steps} currentStep={2} />)

    const listItems = screen.getAllByRole('listitem')
    const currentStep = listItems[1]

    // Current step should have data-status="current"
    expect(currentStep).toHaveAttribute('data-status', 'current')

    // Current step should be visually distinct (we check for the step title)
    expect(currentStep).toHaveTextContent('Map Roles')
  })

  it('dims upcoming steps', () => {
    render(<StepIndicator steps={steps} currentStep={2} />)

    const listItems = screen.getAllByRole('listitem')

    // Upcoming steps should have data-status="upcoming"
    expect(listItems[2]).toHaveAttribute('data-status', 'upcoming')
    expect(listItems[3]).toHaveAttribute('data-status', 'upcoming')
    expect(listItems[4]).toHaveAttribute('data-status', 'upcoming')

    // Upcoming steps should have opacity class for dimming
    expect(listItems[2]).toHaveClass('opacity-50')
    expect(listItems[3]).toHaveClass('opacity-50')
    expect(listItems[4]).toHaveClass('opacity-50')
  })

  it('supports vertical orientation', () => {
    const { container } = render(
      <StepIndicator steps={steps} currentStep={2} orientation="vertical" />
    )

    // Container should have flex-col class for vertical orientation
    const list = container.querySelector('ul')
    expect(list).toHaveClass('flex-col')
  })

  it('uses horizontal orientation by default', () => {
    const { container } = render(<StepIndicator steps={steps} currentStep={2} />)

    // Container should not have flex-col class by default
    const list = container.querySelector('ul')
    expect(list).not.toHaveClass('flex-col')
  })

  it('renders with explicit horizontal orientation', () => {
    const { container } = render(
      <StepIndicator steps={steps} currentStep={2} orientation="horizontal" />
    )

    // Container should not have flex-col class
    const list = container.querySelector('ul')
    expect(list).not.toHaveClass('flex-col')
  })
})
