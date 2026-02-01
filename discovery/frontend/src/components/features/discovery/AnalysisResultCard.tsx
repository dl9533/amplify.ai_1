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
  HIGH: 'bg-red-100 text-red-800',
  MEDIUM: 'bg-yellow-100 text-yellow-800',
  LOW: 'bg-green-100 text-green-800',
}

export function AnalysisResultCard({ result }: AnalysisResultCardProps) {
  const badgeColor = priorityTierColors[result.priorityTier] || 'bg-gray-100 text-gray-800'

  return (
    <div
      data-testid="analysis-result-card"
      className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900">{result.name}</h3>
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
              <p className="text-sm text-gray-500">Exposure Score</p>
              <p className="text-xl font-bold text-gray-900">
                {Math.round(result.exposureScore * 100)}%
              </p>
            </div>
          )}
          {result.impactScore !== undefined && (
            <div>
              <p className="text-sm text-gray-500">Impact Score</p>
              <p className="text-xl font-bold text-gray-900">
                {Math.round(result.impactScore * 100)}%
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
