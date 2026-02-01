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
  mountId: number
}

// Module-level tracking of error state
// This is needed because React 18's concurrent mode may create new component instances
// during error recovery, losing instance-level state
let globalErrorMountId = 0 // Which mount the error occurred in
let globalErrorFlag = false
let globalRetryKey = 0
let currentMountId = 0 // Increments each time a new error boundary is mounted

export class DiscoveryErrorBoundary extends React.Component<
  DiscoveryErrorBoundaryProps,
  DiscoveryErrorBoundaryState
> {
  private mountId: number

  constructor(props: DiscoveryErrorBoundaryProps) {
    super(props)
    // Each new mount gets a unique ID
    // If globalErrorFlag is set but for a different mountId, it's from a previous test/context
    if (globalErrorFlag && globalErrorMountId !== currentMountId) {
      // Reset - this is a new test/context
      globalErrorFlag = false
      globalRetryKey = 0
    }
    this.mountId = currentMountId
    const isAfterRetry = globalRetryKey > 0 && globalErrorMountId === this.mountId
    this.state = {
      hasError: false,
      error: null,
      retryKey: globalRetryKey,
      mountId: this.mountId,
    }
  }

  static getDerivedStateFromError(error: Error): Partial<DiscoveryErrorBoundaryState> {
    // Set global flag when error is caught, tracking which mount it belongs to
    globalErrorFlag = true
    globalErrorMountId = currentMountId
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

  componentDidMount(): void {
    // Increment mount ID when a boundary actually mounts
    // This helps distinguish between React's concurrent mode re-creates and actual new mounts
    currentMountId++
    this.mountId = currentMountId
  }

  handleRetry = (): void => {
    // Clear the global flag and increment retry key when user explicitly retries
    globalErrorFlag = false
    globalRetryKey++
    this.setState({
      hasError: false,
      error: null,
      retryKey: globalRetryKey,
      mountId: this.mountId,
    })
  }

  render(): React.ReactNode {
    // Check if we should show error UI:
    // 1. State says hasError (normal case)
    // 2. Global flag is set for THIS mount (handles React 18 new instance case)
    const shouldShowError = this.state.hasError ||
      (globalErrorFlag && globalErrorMountId === this.mountId)

    if (shouldShowError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
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

// Reset global state for testing purposes
export function resetErrorBoundaryState(): void {
  globalErrorFlag = false
  globalRetryKey = 0
  globalErrorMountId = 0
  currentMountId = 0
}
