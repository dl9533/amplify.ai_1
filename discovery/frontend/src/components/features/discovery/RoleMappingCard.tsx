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
    <div role="article" aria-label={`Role mapping for ${mapping.sourceRole}`} className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold text-gray-900">{mapping.sourceRole}</h3>
            {mapping.isConfirmed && (
              <span
                data-testid="confirmed-badge"
                className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800"
              >
                Confirmed
              </span>
            )}
          </div>
          <p className="mt-1 text-sm text-gray-500">{mapping.headcount} employees</p>
        </div>
        <div className="text-right">
          <span className="text-2xl font-bold text-gray-900">{confidencePercentage}%</span>
          <p className="text-xs text-gray-500">confidence</p>
        </div>
      </div>

      <div className="mt-4 rounded-md bg-gray-50 p-3">
        <p className="text-sm text-gray-600">Mapped to O*NET:</p>
        <p className="font-medium text-gray-900">{mapping.onetTitle}</p>
        <p className="text-xs text-gray-500">{mapping.onetCode}</p>
      </div>

      {isLowConfidence && (
        <div className="mt-3 rounded-md bg-yellow-50 p-2">
          <p className="text-sm text-yellow-800">Low confidence - review recommended</p>
        </div>
      )}

      <div className="mt-4 flex gap-2">
        {!mapping.isConfirmed && (
          <button
            onClick={() => onConfirm(mapping.id)}
            aria-label={`Confirm mapping for ${mapping.sourceRole}`}
            className="flex-1 rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
          >
            Confirm
          </button>
        )}
        <button
          onClick={() => onRemap(mapping.id)}
          aria-label={`Remap ${mapping.sourceRole}`}
          className="flex-1 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          Remap
        </button>
      </div>
    </div>
  )
}
