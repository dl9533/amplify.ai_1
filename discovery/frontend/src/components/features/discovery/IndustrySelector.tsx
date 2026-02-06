import { useState, useEffect, useMemo } from 'react'
import { IconChevronDown, IconCheck, IconBuilding } from '../../ui/Icons'

export interface NaicsSector {
  code: string
  label: string
}

export interface Supersector {
  code: string
  label: string
  sectors: NaicsSector[]
}

export interface IndustrySelectorProps {
  /**
   * List of supersectors with their NAICS sectors.
   */
  supersectors: Supersector[]
  /**
   * Currently selected NAICS sector code (2-digit).
   */
  value: string | null
  /**
   * Callback when a sector is selected.
   */
  onChange: (naicsSector: string) => void
  /**
   * Whether the selector is disabled.
   */
  disabled?: boolean
  /**
   * Whether a save is in progress.
   */
  isSaving?: boolean
  /**
   * Error message to display.
   */
  error?: string | null
}

export function IndustrySelector({
  supersectors,
  value,
  onChange,
  disabled = false,
  isSaving = false,
  error = null,
}: IndustrySelectorProps) {
  // Find the supersector containing the selected sector
  const findSupersectorForSector = (sectorCode: string | null): string | null => {
    if (!sectorCode) return null
    for (const ss of supersectors) {
      if (ss.sectors.some((s) => s.code === sectorCode)) {
        return ss.code
      }
    }
    return null
  }

  const [selectedSupersector, setSelectedSupersector] = useState<string | null>(
    findSupersectorForSector(value)
  )

  // Update supersector when value changes externally
  useEffect(() => {
    const supersectorCode = findSupersectorForSector(value)
    if (supersectorCode !== selectedSupersector) {
      setSelectedSupersector(supersectorCode)
    }
  }, [value, supersectors])

  // Get available sectors for selected supersector
  const availableSectors = useMemo(() => {
    if (!selectedSupersector) return []
    const ss = supersectors.find((s) => s.code === selectedSupersector)
    return ss?.sectors || []
  }, [selectedSupersector, supersectors])

  // Get labels for display
  const selectedSupersectorLabel = useMemo(() => {
    if (!selectedSupersector) return null
    return supersectors.find((s) => s.code === selectedSupersector)?.label
  }, [selectedSupersector, supersectors])

  const selectedSectorLabel = useMemo(() => {
    if (!value) return null
    for (const ss of supersectors) {
      const sector = ss.sectors.find((s) => s.code === value)
      if (sector) return sector.label
    }
    return null
  }, [value, supersectors])

  const handleSupersectorChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newSupersector = e.target.value || null
    setSelectedSupersector(newSupersector)
    // Clear sector selection when supersector changes
    // Don't call onChange yet - wait for sector selection
  }

  const handleSectorChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newSector = e.target.value
    if (newSector) {
      onChange(newSector)
    }
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2 mb-2">
        <IconBuilding size={20} className="text-accent" />
        <h3 className="text-base font-semibold text-default">Company Industry</h3>
        {value && (
          <span className="ml-auto text-xs text-success flex items-center gap-1">
            <IconCheck size={14} />
            Selected
          </span>
        )}
      </div>

      <p className="text-sm text-muted mb-4">
        Select your company&apos;s primary industry to improve role mapping accuracy.
        This helps match job titles to the most relevant O*NET occupations.
      </p>

      {/* Supersector dropdown */}
      <div>
        <label
          htmlFor="supersector-select"
          className="block text-sm font-medium text-default mb-1.5"
        >
          Industry Category
        </label>
        <div className="relative">
          <select
            id="supersector-select"
            value={selectedSupersector || ''}
            onChange={handleSupersectorChange}
            disabled={disabled || isSaving}
            className={`
              w-full px-3 py-2.5 pr-10
              bg-bg-surface border border-border rounded-lg
              text-default text-sm
              appearance-none cursor-pointer
              focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent
              disabled:opacity-50 disabled:cursor-not-allowed
              transition-colors
            `}
          >
            <option value="">Select an industry category...</option>
            {supersectors.map((ss) => (
              <option key={ss.code} value={ss.code}>
                {ss.label}
              </option>
            ))}
          </select>
          <IconChevronDown
            size={16}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted pointer-events-none"
          />
        </div>
      </div>

      {/* Sector dropdown - only show when supersector is selected */}
      {selectedSupersector && availableSectors.length > 0 && (
        <div>
          <label
            htmlFor="sector-select"
            className="block text-sm font-medium text-default mb-1.5"
          >
            Specific Industry
          </label>
          <div className="relative">
            <select
              id="sector-select"
              value={value || ''}
              onChange={handleSectorChange}
              disabled={disabled || isSaving}
              className={`
                w-full px-3 py-2.5 pr-10
                bg-bg-surface border border-border rounded-lg
                text-default text-sm
                appearance-none cursor-pointer
                focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent
                disabled:opacity-50 disabled:cursor-not-allowed
                transition-colors
              `}
            >
              <option value="">Select a specific industry...</option>
              {availableSectors.map((sector) => (
                <option key={sector.code} value={sector.code}>
                  {sector.label}
                </option>
              ))}
            </select>
            <IconChevronDown
              size={16}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted pointer-events-none"
            />
          </div>
        </div>
      )}

      {/* Selected summary */}
      {value && selectedSupersectorLabel && selectedSectorLabel && (
        <div className="p-3 bg-success/10 border border-success/20 rounded-lg">
          <p className="text-sm text-default">
            <span className="font-medium">Selected:</span>{' '}
            {selectedSupersectorLabel} &rarr; {selectedSectorLabel}
          </p>
          <p className="text-xs text-muted mt-1">
            NAICS Sector Code: {value}
          </p>
        </div>
      )}

      {/* Saving indicator */}
      {isSaving && (
        <p className="text-xs text-accent animate-pulse">Saving...</p>
      )}

      {/* Error message */}
      {error && (
        <p className="text-xs text-danger">{error}</p>
      )}
    </div>
  )
}
