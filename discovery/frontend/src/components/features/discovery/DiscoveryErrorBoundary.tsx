import React from 'react'
import { Link } from 'react-router-dom'

export interface DiscoveryErrorBoundaryProps {
  children: React.ReactNode
  sessionId?: string
}

interface DiscoveryErrorBoundaryState {
  hasError: boolean
  error: Error | null
  retryKey: number
}

export class DiscoveryErrorBoundary extends React.Component<
  DiscoveryErrorBoundaryProps,
  DiscoveryErrorBoundaryState
> {
  private errorContainerRef: React.RefObject<HTMLDivElement>

  constructor(props: DiscoveryErrorBoundaryProps) {
    super(props)
    this.errorContainerRef = React.createRef()
    this.state = {
      hasError: false,
      error: null,
      retryKey: 0,
    }
  }

  static getDerivedStateFromError(error: Error): Partial<DiscoveryErrorBoundaryState> {
    // Log error in static method as componentDidCatch may not be called in React 18 concurrent mode
    console.error('[Discovery Error]', error)
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    const { sessionId } = this.props

    // Log error with session context
    if (sessionId) {
      console.error(`[Discovery Error] Session: ${sessionId}`, error, errorInfo)
    } else {
      console.error('[Discovery Error]', error, errorInfo)
    }
  }

  componentDidUpdate(_prevProps: DiscoveryErrorBoundaryProps, prevState: DiscoveryErrorBoundaryState): void {
    // Focus management for accessibility - focus the error container when error occurs
    if (this.state.hasError && !prevState.hasError && this.errorContainerRef.current) {
      this.errorContainerRef.current.focus()
    }
  }

  handleRetry = (): void => {
    this.setState((prevState) => ({
      hasError: false,
      error: null,
      retryKey: prevState.retryKey + 1,
    }))
  }

  render(): React.ReactNode {
    if (this.state.hasError) {
      return (
        <div
          ref={this.errorContainerRef}
          role="alert"
          aria-live="assertive"
          tabIndex={-1}
          className="flex flex-col items-center justify-center min-h-[400px] p-8"
        >
          <div className="text-center max-w-md">
            <h2 className="text-xl font-semibold text-foreground mb-2">
              Something went wrong
            </h2>
            <p className="text-foreground-muted mb-6">
              An unexpected error occurred. You can try again or go back to your sessions.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                onClick={this.handleRetry}
                className="btn-primary btn-md rounded-md"
              >
                Retry
              </button>
              <Link
                to="/discovery"
                className="btn-secondary btn-md rounded-md text-center"
              >
                Back to Sessions
              </Link>
            </div>
          </div>
        </div>
      )
    }

    return (
      <React.Fragment key={this.state.retryKey}>
        {this.props.children}
      </React.Fragment>
    )
  }
}
