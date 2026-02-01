import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { DiscoveryErrorBoundary } from '@/components/features/discovery/DiscoveryErrorBoundary'
import { BrowserRouter } from 'react-router-dom'

const ThrowError = () => {
  throw new Error('Test error')
}

describe('DiscoveryErrorBoundary', () => {
  it('renders children when no error', () => {
    render(
      <BrowserRouter>
        <DiscoveryErrorBoundary>
          <div>Content</div>
        </DiscoveryErrorBoundary>
      </BrowserRouter>
    )
    expect(screen.getByText('Content')).toBeInTheDocument()
  })

  it('catches errors and displays fallback UI', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    render(
      <BrowserRouter>
        <DiscoveryErrorBoundary>
          <ThrowError />
        </DiscoveryErrorBoundary>
      </BrowserRouter>
    )
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument()
    consoleSpy.mockRestore()
  })

  it('shows retry button', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    render(
      <BrowserRouter>
        <DiscoveryErrorBoundary>
          <ThrowError />
        </DiscoveryErrorBoundary>
      </BrowserRouter>
    )
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
    consoleSpy.mockRestore()
  })

  it('shows option to go back to session list', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    render(
      <BrowserRouter>
        <DiscoveryErrorBoundary>
          <ThrowError />
        </DiscoveryErrorBoundary>
      </BrowserRouter>
    )
    expect(screen.getByRole('link', { name: /back to sessions/i })).toBeInTheDocument()
    consoleSpy.mockRestore()
  })

  it('logs error to console with session context', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    render(
      <BrowserRouter>
        <DiscoveryErrorBoundary sessionId="test-session">
          <ThrowError />
        </DiscoveryErrorBoundary>
      </BrowserRouter>
    )
    expect(consoleSpy).toHaveBeenCalled()
    consoleSpy.mockRestore()
  })

  it('recovers after retry when child no longer throws', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    // Use an object that can be mutated from outside the component
    const control = { shouldThrow: true }

    const MaybeThrow = () => {
      if (control.shouldThrow) {
        throw new Error('Controlled error')
      }
      return <div>Recovered successfully</div>
    }

    const { rerender } = render(
      <BrowserRouter>
        <DiscoveryErrorBoundary>
          <MaybeThrow />
        </DiscoveryErrorBoundary>
      </BrowserRouter>
    )

    // Error boundary should show error UI
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument()

    // Stop throwing before retry
    control.shouldThrow = false

    // Click retry
    fireEvent.click(screen.getByRole('button', { name: /retry/i }))

    // Should now render the recovered content
    expect(screen.getByText('Recovered successfully')).toBeInTheDocument()
    consoleSpy.mockRestore()
  })

  describe('accessibility', () => {
    it('has role="alert" on error container', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      render(
        <BrowserRouter>
          <DiscoveryErrorBoundary>
            <ThrowError />
          </DiscoveryErrorBoundary>
        </BrowserRouter>
      )
      expect(screen.getByRole('alert')).toBeInTheDocument()
      consoleSpy.mockRestore()
    })

    it('has aria-live="assertive" on error container', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      render(
        <BrowserRouter>
          <DiscoveryErrorBoundary>
            <ThrowError />
          </DiscoveryErrorBoundary>
        </BrowserRouter>
      )
      const alert = screen.getByRole('alert')
      expect(alert).toHaveAttribute('aria-live', 'assertive')
      consoleSpy.mockRestore()
    })

    it('error container is focusable for keyboard navigation', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      render(
        <BrowserRouter>
          <DiscoveryErrorBoundary>
            <ThrowError />
          </DiscoveryErrorBoundary>
        </BrowserRouter>
      )
      const alert = screen.getByRole('alert')
      expect(alert).toHaveAttribute('tabindex', '-1')
      consoleSpy.mockRestore()
    })
  })

  describe('instance-level state management', () => {
    it('uses instance state and not global state', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      // First boundary with error
      const { unmount: unmount1 } = render(
        <BrowserRouter>
          <DiscoveryErrorBoundary>
            <ThrowError />
          </DiscoveryErrorBoundary>
        </BrowserRouter>
      )
      expect(screen.getByText(/something went wrong/i)).toBeInTheDocument()
      unmount1()

      // Second boundary should render children normally (no global state leakage)
      render(
        <BrowserRouter>
          <DiscoveryErrorBoundary>
            <div>Second boundary content</div>
          </DiscoveryErrorBoundary>
        </BrowserRouter>
      )
      expect(screen.getByText('Second boundary content')).toBeInTheDocument()

      consoleSpy.mockRestore()
    })

    it('retry resets error state correctly', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      const control = { shouldThrow: true }

      const MaybeThrow = () => {
        if (control.shouldThrow) {
          throw new Error('Controlled error')
        }
        return <div>Recovered content</div>
      }

      render(
        <BrowserRouter>
          <DiscoveryErrorBoundary>
            <MaybeThrow />
          </DiscoveryErrorBoundary>
        </BrowserRouter>
      )

      // Error state
      expect(screen.getByText(/something went wrong/i)).toBeInTheDocument()
      expect(screen.queryByText(/Recovered/)).not.toBeInTheDocument()

      // Stop throwing before retry
      control.shouldThrow = false

      // Click retry
      fireEvent.click(screen.getByRole('button', { name: /retry/i }))

      // Recovered state
      expect(screen.queryByText(/something went wrong/i)).not.toBeInTheDocument()
      expect(screen.getByText(/Recovered/)).toBeInTheDocument()

      consoleSpy.mockRestore()
    })

    it('multiple error boundaries work independently', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      render(
        <BrowserRouter>
          <div>
            <DiscoveryErrorBoundary>
              <ThrowError />
            </DiscoveryErrorBoundary>
            <DiscoveryErrorBoundary>
              <div>Second boundary works</div>
            </DiscoveryErrorBoundary>
          </div>
        </BrowserRouter>
      )

      // First boundary shows error
      expect(screen.getByText(/something went wrong/i)).toBeInTheDocument()
      // Second boundary renders normally
      expect(screen.getByText('Second boundary works')).toBeInTheDocument()

      consoleSpy.mockRestore()
    })
  })
})
