import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DiscoveryLayout } from '@/components/features/discovery'

describe('DiscoveryLayout', () => {
  it('renders the layout with header and main content area', () => {
    render(
      <DiscoveryLayout>
        <div data-testid="child-content">Test Content</div>
      </DiscoveryLayout>
    )

    // Should have a main content area
    const mainElement = screen.getByRole('main')
    expect(mainElement).toBeInTheDocument()

    // Children should be rendered within the layout
    expect(screen.getByTestId('child-content')).toBeInTheDocument()
    expect(screen.getByText('Test Content')).toBeInTheDocument()
  })

  it('renders the step indicator in sidebar', () => {
    render(
      <DiscoveryLayout currentStep={2} totalSteps={5}>
        <div>Content</div>
      </DiscoveryLayout>
    )

    // Step indicator should have navigation role with aria-label containing "steps"
    const stepIndicator = screen.getByRole('navigation', { name: /steps/i })
    expect(stepIndicator).toBeInTheDocument()

    // Should display step information
    expect(screen.getByText(/step 2/i)).toBeInTheDocument()
    expect(screen.getByText(/of 5/i)).toBeInTheDocument()
  })

  it('renders the chat panel in sidebar', () => {
    render(
      <DiscoveryLayout>
        <div>Content</div>
      </DiscoveryLayout>
    )

    // Chat panel should have complementary role with aria-label containing "chat"
    const chatPanel = screen.getByRole('complementary', { name: /chat/i })
    expect(chatPanel).toBeInTheDocument()
  })

  it('applies correct grid layout classes', () => {
    const { container } = render(
      <DiscoveryLayout>
        <div>Content</div>
      </DiscoveryLayout>
    )

    // Layout should use CSS grid
    const layoutElement = container.firstChild as HTMLElement
    expect(layoutElement).toHaveClass('grid')
  })

  it('shows session title when provided', () => {
    render(
      <DiscoveryLayout sessionTitle="My Discovery Session">
        <div>Content</div>
      </DiscoveryLayout>
    )

    expect(screen.getByText('My Discovery Session')).toBeInTheDocument()
  })

  it('does not show session title when not provided', () => {
    render(
      <DiscoveryLayout>
        <div>Content</div>
      </DiscoveryLayout>
    )

    // Default session title area should not be rendered or be empty
    const sessionTitle = screen.queryByRole('heading', { level: 1 })
    expect(sessionTitle).not.toBeInTheDocument()
  })

  it('renders with default step values when not provided', () => {
    render(
      <DiscoveryLayout>
        <div>Content</div>
      </DiscoveryLayout>
    )

    // Step indicator should still be present even without explicit step props
    const stepIndicator = screen.getByRole('navigation', { name: /steps/i })
    expect(stepIndicator).toBeInTheDocument()
  })
})
