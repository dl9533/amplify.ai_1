import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useRoleMappings, RoleMapping } from '@/hooks/useRoleMappings'

interface RoleMappingRowProps {
  mapping: RoleMapping
  onConfirm: (id: string) => void
}

function RoleMappingRow({ mapping, onConfirm }: RoleMappingRowProps) {
  return (
    <div className="flex items-center justify-between p-4 border border-border rounded-lg bg-background">
      <div className="flex-1">
        <h3 className="font-medium text-foreground">{mapping.roleName}</h3>
        <p className="text-sm text-foreground-muted">
          {mapping.onetTitle} ({mapping.onetCode})
        </p>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-sm font-medium text-foreground">{mapping.confidence}%</span>
        {mapping.confirmed ? (
          <span
            data-testid="confirmed-badge"
            className="px-3 py-1 text-sm font-medium text-success bg-success/10 rounded-full"
          >
            Confirmed
          </span>
        ) : (
          <button
            onClick={() => onConfirm(mapping.id)}
            className="btn-primary btn-md rounded-lg"
          >
            Confirm
          </button>
        )}
      </div>
    </div>
  )
}

export function MapRolesStep() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const { mappings, isLoading, error, confirmMapping, bulkConfirm } = useRoleMappings(sessionId)
  const [searchValue, setSearchValue] = useState('')
  const [confirmationMessage, setConfirmationMessage] = useState('')

  const handleConfirm = (id: string) => {
    confirmMapping(id)
    const mapping = mappings.find((m) => m.id === id)
    if (mapping) {
      setConfirmationMessage(`Confirmed mapping for ${mapping.roleName}`)
    }
  }

  const handleBulkConfirm = (threshold: number) => {
    const count = mappings.filter((m) => m.confidence >= threshold && !m.confirmed).length
    bulkConfirm(threshold)
    setConfirmationMessage(`Confirmed ${count} mappings above ${threshold}% confidence`)
  }

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchValue(e.target.value)
    // Search functionality to be connected to O*NET API in future implementation
  }

  if (!sessionId) {
    return (
      <div className="flex items-center justify-center p-8">
        <span className="text-destructive" role="alert">
          Error: Session ID is required. Please start a new discovery session.
        </span>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <span className="text-foreground-muted">Loading role mappings...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center p-8">
        <span className="text-destructive" role="alert">
          Error: {error}
        </span>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Aria-live region for screen reader announcements */}
      <div aria-live="polite" aria-atomic="true" className="sr-only">
        {confirmationMessage}
      </div>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-foreground">Map Your Roles</h1>
        <p className="mt-2 text-foreground-muted">
          Review and confirm the O*NET occupation mappings for your roles.
        </p>
      </div>

      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <label htmlFor="onet-search" className="sr-only">
            Search O*NET
          </label>
          <input
            id="onet-search"
            type="text"
            role="combobox"
            aria-label="Search O*NET"
            placeholder="Search O*NET occupations..."
            value={searchValue}
            onChange={handleSearchChange}
            className="input"
          />
        </div>
        <button
          onClick={() => handleBulkConfirm(80)}
          className="btn-secondary btn-md rounded-lg"
        >
          Confirm all above 80%
        </button>
      </div>

      <div className="space-y-3">
        {mappings.map((mapping) => (
          <RoleMappingRow
            key={mapping.id}
            mapping={mapping}
            onConfirm={handleConfirm}
          />
        ))}
      </div>

      {mappings.length === 0 && (
        <div className="text-center py-8 text-foreground-muted">
          No role mappings found. Upload a file to get started.
        </div>
      )}
    </div>
  )
}
