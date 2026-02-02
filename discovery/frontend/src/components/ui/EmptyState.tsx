import { ReactNode } from 'react'

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  description?: string
  action?: ReactNode
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      {icon && (
        <div className="w-14 h-14 rounded-full bg-bg-muted flex items-center justify-center text-subtle mb-4">
          {icon}
        </div>
      )}
      <h3 className="text-lg font-semibold font-display text-default mb-1">{title}</h3>
      {description && <p className="text-sm text-muted max-w-sm mb-4">{description}</p>}
      {action}
    </div>
  )
}

// Loading skeleton variant
export function LoadingState({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <div className="relative w-10 h-10 mb-4">
        <div className="absolute inset-0 border-2 border-accent/20 rounded-full" />
        <div className="absolute inset-0 border-2 border-transparent border-t-accent rounded-full animate-spin" />
      </div>
      <p className="text-sm text-muted">{message}</p>
    </div>
  )
}

// Error state variant
interface ErrorStateProps {
  title?: string
  message?: string
  retry?: () => void
}

export function ErrorState({
  title = 'Something went wrong',
  message = 'An unexpected error occurred. Please try again.',
  retry,
}: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <div className="w-14 h-14 rounded-full bg-destructive/10 flex items-center justify-center text-destructive mb-4">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" x2="12" y1="8" y2="12" />
          <line x1="12" x2="12.01" y1="16" y2="16" />
        </svg>
      </div>
      <h3 className="text-lg font-semibold font-display text-default mb-1">{title}</h3>
      <p className="text-sm text-muted max-w-sm mb-4">{message}</p>
      {retry && (
        <button className="btn-secondary btn-sm" onClick={retry}>
          Try again
        </button>
      )}
    </div>
  )
}
