import { ReactNode } from 'react'

interface BadgeProps {
  children: ReactNode
  variant?: 'default' | 'accent' | 'success' | 'warning' | 'destructive'
  size?: 'sm' | 'md'
  dot?: boolean
}

export function Badge({
  children,
  variant = 'default',
  size = 'sm',
  dot = false,
}: BadgeProps) {
  const variantClasses = {
    default: 'bg-bg-muted text-muted',
    accent: 'bg-accent/15 text-accent',
    success: 'bg-success/15 text-success',
    warning: 'bg-warning/15 text-warning',
    destructive: 'bg-destructive/15 text-destructive',
  }

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
  }

  const dotColors = {
    default: 'bg-fg-subtle',
    accent: 'bg-accent',
    success: 'bg-success',
    warning: 'bg-warning',
    destructive: 'bg-destructive',
  }

  return (
    <span
      className={`
        inline-flex items-center gap-1.5 font-medium font-display rounded-full
        ${variantClasses[variant]} ${sizeClasses[size]}
      `}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full ${dotColors[variant]}`} />}
      {children}
    </span>
  )
}

// Status badge for session states
type SessionStatus = 'draft' | 'in_progress' | 'completed' | 'archived'

interface StatusBadgeProps {
  status: SessionStatus
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const config: Record<SessionStatus, { label: string; variant: BadgeProps['variant'] }> = {
    draft: { label: 'Draft', variant: 'default' },
    in_progress: { label: 'In Progress', variant: 'accent' },
    completed: { label: 'Completed', variant: 'success' },
    archived: { label: 'Archived', variant: 'default' },
  }

  const { label, variant } = config[status] || config.draft

  return (
    <Badge variant={variant} dot>
      {label}
    </Badge>
  )
}

// Priority tier badge
type PriorityTier = 'HIGH' | 'MEDIUM' | 'LOW'

interface TierBadgeProps {
  tier: PriorityTier
  showLabel?: boolean
}

export function TierBadge({ tier, showLabel = true }: TierBadgeProps) {
  const config: Record<PriorityTier, { label: string; variant: BadgeProps['variant'] }> = {
    HIGH: { label: 'High', variant: 'success' },
    MEDIUM: { label: 'Medium', variant: 'warning' },
    LOW: { label: 'Low', variant: 'default' },
  }

  const { label, variant } = config[tier] || config.LOW

  return (
    <Badge variant={variant} size="sm">
      {showLabel ? label : tier.charAt(0)}
    </Badge>
  )
}

// Confidence badge for role mappings
interface ConfidenceBadgeProps {
  score: number // 0-1
}

export function ConfidenceBadge({ score }: ConfidenceBadgeProps) {
  const percentage = Math.round(score * 100)

  let variant: BadgeProps['variant'] = 'default'
  if (score >= 0.85) variant = 'success'
  else if (score >= 0.6) variant = 'warning'
  else variant = 'destructive'

  return (
    <Badge variant={variant} size="sm">
      {percentage}%
    </Badge>
  )
}

// Phase badge for roadmap
type Phase = 'NOW' | 'NEXT' | 'LATER'

interface PhaseBadgeProps {
  phase: Phase
}

export function PhaseBadge({ phase }: PhaseBadgeProps) {
  const config: Record<Phase, { label: string; variant: BadgeProps['variant'] }> = {
    NOW: { label: 'Now', variant: 'success' },
    NEXT: { label: 'Next', variant: 'accent' },
    LATER: { label: 'Later', variant: 'default' },
  }

  const { label, variant } = config[phase] || config.LATER

  return (
    <Badge variant={variant} size="sm">
      {label}
    </Badge>
  )
}
