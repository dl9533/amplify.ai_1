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

  it('preserves session state after retry', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    let shouldThrow = true
    const MaybeThrow = () => {
      if (shouldThrow) {
        shouldThrow = false
        throw new Error('First render error')
      }
      return <div>Recovered</div>
    }
    render(
      <BrowserRouter>
        <DiscoveryErrorBoundary>
          <MaybeThrow />
        </DiscoveryErrorBoundary>
      </BrowserRouter>
    )
    fireEvent.click(screen.getByRole('button', { name: /retry/i }))
    expect(screen.getByText('Recovered')).toBeInTheDocument()
    consoleSpy.mockRestore()
  })
})
