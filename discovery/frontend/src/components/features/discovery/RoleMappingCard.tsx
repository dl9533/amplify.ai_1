export interface RoleMapping {
  id: string
  sourceRole: string
  onetCode: string
  onetTitle: string
  confidenceScore: number
  isConfirmed: boolean
  headcount: number
}

export interface RoleMappingCardProps {
  mapping: RoleMapping
  onConfirm: (id: string) => void
  onRemap: (id: string) => void
}

export function RoleMappingCard({ mapping, onConfirm, onRemap }: RoleMappingCardProps) {
  const confidencePercentage = Math.round(mapping.confidenceScore * 100)
  const isLowConfidence = mapping.confidenceScore < 0.5

  return (
    <div
      role="article"
      aria-label={`Role mapping for ${mapping.sourceRole}`}
      className="card p-4"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold text-foreground">{mapping.sourceRole}</h3>
            {mapping.isConfirmed && (
              <span
                data-testid="confirmed-badge"
                className="inline-flex items-center rounded-full bg-success/10 px-2.5 py-0.5 text-xs font-medium text-success"
              >
                Confirmed
              </span>
            )}
          </div>
          <p className="mt-1 text-sm text-foreground-muted">{mapping.headcount} employees</p>
        </div>
        <div className="text-right">
          <span className="text-2xl font-bold text-foreground tabular-nums">{confidencePercentage}%</span>
          <p className="text-xs text-foreground-subtle">confidence</p>
        </div>
      </div>

      <div className="mt-4 rounded-md bg-background-muted p-3">
        <p className="text-sm text-foreground-muted">Mapped to O*NET:</p>
        <p className="font-medium text-foreground">{mapping.onetTitle}</p>
        <p className="text-xs text-foreground-subtle font-mono">{mapping.onetCode}</p>
      </div>

      {isLowConfidence && (
        <div className="mt-3 rounded-md bg-warning/10 border border-warning/20 p-2">
          <p className="text-sm text-warning">Low confidence - review recommended</p>
        </div>
      )}

      <div className="mt-4 flex gap-2">
        {!mapping.isConfirmed && (
          <button
            onClick={() => onConfirm(mapping.id)}
            aria-label={`Confirm mapping for ${mapping.sourceRole}`}
            className="flex-1 rounded-md bg-success text-success-foreground px-4 py-2 text-sm font-medium hover:bg-success/90 transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          >
            Confirm
          </button>
        )}
        <button
          onClick={() => onRemap(mapping.id)}
          aria-label={`Remap ${mapping.sourceRole}`}
          className="btn-secondary btn-md flex-1 rounded-md"
        >
          Remap
        </button>
      </div>
    </div>
  )
}
