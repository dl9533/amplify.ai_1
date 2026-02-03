import { ReactNode, useState } from 'react'

interface TooltipProps {
  content: ReactNode
  children: ReactNode
  position?: 'top' | 'bottom' | 'left' | 'right'
  maxWidth?: string
}

export function Tooltip({
  content,
  children,
  position = 'top',
  maxWidth = '300px',
}: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false)

  const positionClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  }

  const arrowClasses = {
    top: 'top-full left-1/2 -translate-x-1/2 border-t-fg-default border-x-transparent border-b-transparent',
    bottom: 'bottom-full left-1/2 -translate-x-1/2 border-b-fg-default border-x-transparent border-t-transparent',
    left: 'left-full top-1/2 -translate-y-1/2 border-l-fg-default border-y-transparent border-r-transparent',
    right: 'right-full top-1/2 -translate-y-1/2 border-r-fg-default border-y-transparent border-l-transparent',
  }

  if (!content) return <>{children}</>

  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
      onFocus={() => setIsVisible(true)}
      onBlur={() => setIsVisible(false)}
    >
      {children}
      {isVisible && (
        <div
          className={`
            absolute z-50 px-3 py-2 text-sm
            bg-fg-default text-bg-base rounded-lg shadow-lg
            animate-fade-in whitespace-normal
            ${positionClasses[position]}
          `}
          style={{ maxWidth }}
          role="tooltip"
        >
          {content}
          <div
            className={`
              absolute w-0 h-0
              border-4 ${arrowClasses[position]}
            `}
          />
        </div>
      )}
    </div>
  )
}

// Info icon with tooltip for displaying reasoning
interface InfoTooltipProps {
  content: string
  position?: 'top' | 'bottom' | 'left' | 'right'
}

export function InfoTooltip({ content, position = 'top' }: InfoTooltipProps) {
  if (!content) return null

  return (
    <Tooltip content={content} position={position}>
      <button
        type="button"
        className="
          inline-flex items-center justify-center
          w-5 h-5 rounded-full
          bg-bg-muted text-muted
          hover:bg-accent/20 hover:text-accent
          transition-colors cursor-help
        "
        aria-label="More information"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          className="w-3.5 h-3.5"
        >
          <path
            fillRule="evenodd"
            d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z"
            clipRule="evenodd"
          />
        </svg>
      </button>
    </Tooltip>
  )
}
