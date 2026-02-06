export interface ColumnSchema {
  columns: string[]
  sampleRows: string[][]
}

export interface ColumnMappings {
  role?: string
  department?: string
  lob?: string
  geography?: string
}

export interface ColumnMappingPreviewProps {
  schema: ColumnSchema
  mappings: ColumnMappings
  onMappingChange: (mappings: ColumnMappings) => void
}

type MappingKey = keyof ColumnMappings

const MAPPING_LABELS: Record<MappingKey, string> = {
  role: 'Role column',
  department: 'Department column',
  lob: 'Line of Business column',
  geography: 'Geography column',
}

const REQUIRED_MAPPINGS: MappingKey[] = ['role']

export function ColumnMappingPreview({
  schema,
  mappings,
  onMappingChange,
}: ColumnMappingPreviewProps) {
  const isMapped = (column: string): boolean => {
    return Object.values(mappings).includes(column)
  }

  const handleMappingChange = (key: MappingKey, value: string) => {
    onMappingChange({
      ...mappings,
      [key]: value || undefined,
    })
  }

  return (
    <div className="space-y-4">
      {/* Mapping selectors */}
      <div className="flex flex-wrap gap-4">
        {(Object.keys(MAPPING_LABELS) as MappingKey[]).map((key) => (
          <div key={key} className="flex flex-col">
            <label htmlFor={`mapping-${key}`} className="text-sm font-medium text-foreground mb-1">
              {MAPPING_LABELS[key]}
              {REQUIRED_MAPPINGS.includes(key) && !mappings[key] && (
                <span className="text-destructive ml-1">(Role required)</span>
              )}
            </label>
            <select
              id={`mapping-${key}`}
              aria-label={MAPPING_LABELS[key]}
              value={mappings[key] || ''}
              onChange={(e) => handleMappingChange(key, e.target.value)}
              className="border border-border rounded-md px-3 py-2 text-sm bg-background text-foreground focus:ring-ring focus:border-primary"
            >
              <option value="">Select column...</option>
              {schema.columns.map((column) => (
                <option key={column} value={column}>
                  {column}
                </option>
              ))}
            </select>
          </div>
        ))}
      </div>

      {/* Data preview table */}
      <div className="overflow-x-auto border border-border rounded-lg">
        <table className="min-w-full divide-y divide-border">
          <thead className="bg-background-muted">
            <tr>
              {schema.columns.map((column) => (
                <th
                  key={column}
                  className={`px-4 py-3 text-left text-xs font-medium text-foreground-muted uppercase tracking-wider ${
                    isMapped(column) ? 'bg-primary/10' : ''
                  }`}
                >
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-background divide-y divide-border">
            {schema.sampleRows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {row.map((cell, cellIndex) => (
                  <td
                    key={cellIndex}
                    className={`px-4 py-3 text-sm text-foreground whitespace-nowrap ${
                      isMapped(schema.columns[cellIndex]) ? 'bg-primary/10' : ''
                    }`}
                  >
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
