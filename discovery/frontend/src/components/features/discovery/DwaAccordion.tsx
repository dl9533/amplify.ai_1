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
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
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
          <span className="font-medium text-gray-900">{group.gwaTitle}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">{selectedCount}/{totalCount} selected</span>
          <span
            className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
            title="AI Exposure Score"
          >
            {exposurePercentage}%
          </span>
        </div>
      </button>

      {isOpen && (
        <div
          id={`dwa-panel-${group.gwaId}`}
          className="p-4 bg-white border-t border-gray-200"
        >
          <div className="flex justify-end mb-3">
            <button
              type="button"
              onClick={handleSelectAll}
              disabled={allSelected}
              className={`text-sm font-medium ${
                allSelected
                  ? 'text-gray-400 cursor-not-allowed'
                  : 'text-blue-600 hover:text-blue-800'
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
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  aria-label={dwa.title}
                />
                <label
                  htmlFor={`dwa-${dwa.id}`}
                  className="text-sm text-gray-700 cursor-pointer"
                >
                  <span className="text-gray-400 mr-2">{dwa.dwaId}</span>
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
