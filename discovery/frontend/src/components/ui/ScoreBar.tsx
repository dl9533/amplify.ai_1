interface ScoreBarProps {
  value: number // 0-1
  label?: string
  showValue?: boolean
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'accent' | 'success' | 'warning' | 'tier'
}

export function ScoreBar({
  value,
  label,
  showValue = true,
  size = 'md',
  variant = 'default',
}: ScoreBarProps) {
  const clampedValue = Math.max(0, Math.min(1, value))
  const percentage = Math.round(clampedValue * 100)

  const heights = {
    sm: 'h-1',
    md: 'h-1.5',
    lg: 'h-2',
  }

  // Color based on tier (for priority/exposure scores)
  const getColor = () => {
    if (variant === 'tier') {
      if (clampedValue >= 0.75) return 'bg-success'
      if (clampedValue >= 0.5) return 'bg-warning'
      return 'bg-fg-subtle'
    }
    const colors = {
      default: 'bg-fg-muted',
      accent: 'bg-accent',
      success: 'bg-success',
      warning: 'bg-warning',
    }
    return colors[variant]
  }

  return (
    <div className="w-full">
      {(label || showValue) && (
        <div className="flex justify-between items-center mb-1">
          {label && <span className="text-xs text-muted">{label}</span>}
          {showValue && (
            <span className="text-xs font-medium font-display tabular-nums text-default">
              {percentage}%
            </span>
          )}
        </div>
      )}
      <div className={`w-full ${heights[size]} bg-bg-muted rounded-full overflow-hidden`}>
        <div
          className={`h-full ${getColor()} rounded-full transition-all duration-500 ease-out`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

// Inline score pill for compact display
interface ScorePillProps {
  value: number
  label?: string
  variant?: 'default' | 'tier'
}

export function ScorePill({ value, label, variant = 'default' }: ScorePillProps) {
  const percentage = Math.round(Math.max(0, Math.min(1, value)) * 100)

  const getColorClass = () => {
    if (variant === 'tier') {
      if (value >= 0.75) return 'text-success bg-success/10'
      if (value >= 0.5) return 'text-warning bg-warning/10'
      return 'text-subtle bg-bg-muted'
    }
    return 'text-accent bg-accent/10'
  }

  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium font-display ${getColorClass()}`}>
      {label && <span className="text-muted">{label}</span>}
      <span className="tabular-nums">{percentage}%</span>
    </span>
  )
}

// Mini bar for tables and compact views
interface MiniBarProps {
  value: number
  width?: number
}

export function MiniBar({ value, width = 48 }: MiniBarProps) {
  const percentage = Math.max(0, Math.min(1, value)) * 100

  const getColor = () => {
    if (value >= 0.75) return 'bg-success'
    if (value >= 0.5) return 'bg-warning'
    return 'bg-fg-subtle'
  }

  return (
    <div className="flex items-center gap-2">
      <div
        className="h-1 bg-bg-muted rounded-full overflow-hidden"
        style={{ width }}
      >
        <div
          className={`h-full ${getColor()} rounded-full`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="text-xs font-medium tabular-nums text-muted">
        {Math.round(percentage)}%
      </span>
    </div>
  )
}
