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
  private errorContainerRef: React.RefObject<HTMLDivElement | null>

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
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Something went wrong
            </h2>
            <p className="text-gray-600 mb-6">
              An unexpected error occurred. You can try again or go back to your sessions.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                onClick={this.handleRetry}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Retry
              </button>
              <Link
                to="/discovery"
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 text-center"
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
