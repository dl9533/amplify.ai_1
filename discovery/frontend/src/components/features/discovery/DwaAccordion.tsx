import { useState, useCallback, useMemo } from 'react'

export interface Dwa {
  id: string
  dwaId: string
  title: string
  isSelected: boolean
}

export interface GwaGroup {
  gwaId: string
  gwaTitle: string
  aiExposureScore: number
  dwas: Dwa[]
}

export interface DwaAccordionProps {
  group: GwaGroup
  onDwaToggle: (dwaId: string, isSelected: boolean) => void
  onSelectAllInGroup?: (gwaId: string, dwaIds: string[]) => void
  defaultOpen?: boolean
}

export function DwaAccordion({ group, onDwaToggle, onSelectAllInGroup, defaultOpen = false }: DwaAccordionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  const selectedCount = useMemo(() => group.dwas.filter((dwa) => dwa.isSelected).length, [group.dwas])
  const totalCount = group.dwas.length
  const exposurePercentage = Math.round(group.aiExposureScore * 100)
  const allSelected = selectedCount === totalCount

  const handleSelectAll = useCallback(() => {
    const unselectedDwas = group.dwas.filter((dwa) => !dwa.isSelected)
    if (unselectedDwas.length === 0) return

    if (onSelectAllInGroup) {
      const dwaIds = unselectedDwas.map((dwa) => dwa.id)
      onSelectAllInGroup(group.gwaId, dwaIds)
    } else {
      unselectedDwas.forEach((dwa) => {
        onDwaToggle(dwa.id, true)
      })
    }
  }, [group.dwas, group.gwaId, onDwaToggle, onSelectAllInGroup])

  const handleCheckboxChange = useCallback((dwa: Dwa) => {
    onDwaToggle(dwa.id, !dwa.isSelected)
  }, [onDwaToggle])

  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 bg-background-muted hover:bg-background-accent transition-colors"
        aria-expanded={isOpen}
        aria-controls={`dwa-panel-${group.gwaId}`}
      >
        <div className="flex items-center gap-3">
          <span
            className={`transform transition-transform ${isOpen ? 'rotate-90' : ''}`}
            aria-hidden="true"
          >
            &#9654;
          </span>
          <span className="font-medium text-foreground">{group.gwaTitle}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-foreground-muted">{selectedCount}/{totalCount} selected</span>
          <span
            className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary"
            title="AI Exposure Score"
          >
            {exposurePercentage}%
          </span>
        </div>
      </button>

      {isOpen && (
        <div
          id={`dwa-panel-${group.gwaId}`}
          className="p-4 bg-background border-t border-border"
        >
          <div className="flex justify-end mb-3">
            <button
              type="button"
              onClick={handleSelectAll}
              disabled={allSelected}
              className={`text-sm font-medium ${
                allSelected
                  ? 'text-foreground-subtle cursor-not-allowed'
                  : 'text-primary hover:text-primary/80'
              }`}
              aria-label={`Select all tasks in ${group.gwaTitle}`}
              aria-disabled={allSelected}
            >
              Select all
            </button>
          </div>
          <ul className="space-y-2">
            {group.dwas.map((dwa) => (
              <li key={dwa.id} className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id={`dwa-${dwa.id}`}
                  checked={dwa.isSelected}
                  onChange={() => handleCheckboxChange(dwa)}
                  className="h-4 w-4 text-primary border-border rounded focus:ring-ring"
                  aria-label={dwa.title}
                />
                <label
                  htmlFor={`dwa-${dwa.id}`}
                  className="text-sm text-foreground cursor-pointer"
                >
                  <span className="text-foreground-subtle mr-2">{dwa.dwaId}</span>
                  {dwa.title}
                </label>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
