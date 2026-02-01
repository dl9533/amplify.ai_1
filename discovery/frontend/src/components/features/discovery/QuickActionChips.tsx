export interface ActionChip {
  label: string
  action: string
  variant?: 'primary' | 'secondary' | 'ghost'
}

export interface QuickActionChipsProps {
  chips: ActionChip[]
  onAction: (action: string) => void
  isLoading?: boolean
}

const variantClasses: Record<ActionChip['variant'] & string, string> = {
  primary: 'bg-primary text-primary-foreground hover:bg-primary/90',
  secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
  ghost: 'hover:bg-accent hover:text-accent-foreground',
}

export function QuickActionChips({
  chips,
  onAction,
  isLoading = false,
}: QuickActionChipsProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {chips.map((chip) => {
        const variant = chip.variant || 'secondary'
        return (
          <button
            key={chip.action}
            type="button"
            onClick={() => onAction(chip.action)}
            disabled={isLoading}
            aria-label={chip.label}
            className={`inline-flex items-center rounded-full px-3 py-1.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 ${variantClasses[variant]}`}
          >
            {chip.label}
          </button>
        )
      })}
    </div>
  )
}
