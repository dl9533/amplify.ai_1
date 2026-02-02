export interface AnalysisResult {
  id: string
  name: string
  exposureScore?: number
  impactScore?: number
  priorityTier: 'HIGH' | 'MEDIUM' | 'LOW'
  priorityScore?: number
}

export interface AnalysisResultCardProps {
  result: AnalysisResult
}

const priorityTierColors: Record<string, string> = {
  HIGH: 'bg-destructive/10 text-destructive',
  MEDIUM: 'bg-warning/10 text-warning',
  LOW: 'bg-success/10 text-success',
}

export function AnalysisResultCard({ result }: AnalysisResultCardProps) {
  const badgeColor = priorityTierColors[result.priorityTier] || 'bg-background-muted text-foreground-muted'

  return (
    <div
      data-testid="analysis-result-card"
      className="card p-4"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-foreground">{result.name}</h3>
        </div>
        <span
          className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${badgeColor}`}
        >
          {result.priorityTier}
        </span>
      </div>

      {(result.exposureScore !== undefined || result.impactScore !== undefined) && (
        <div className="mt-3 grid grid-cols-2 gap-4">
          {result.exposureScore !== undefined && (
            <div>
              <p className="text-sm text-foreground-muted">Exposure Score</p>
              <p className="text-xl font-bold text-foreground tabular-nums">
                {Math.round(result.exposureScore * 100)}%
              </p>
            </div>
          )}
          {result.impactScore !== undefined && (
            <div>
              <p className="text-sm text-foreground-muted">Impact Score</p>
              <p className="text-xl font-bold text-foreground tabular-nums">
                {Math.round(result.impactScore * 100)}%
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
