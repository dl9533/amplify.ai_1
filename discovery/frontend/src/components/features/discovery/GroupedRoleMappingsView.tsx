import { useState, useCallback } from 'react'
import { Button } from '../../ui/Button'
import { IconCheck, IconUsers, IconSearch, IconRefresh } from '../../ui/Icons'
import { ScoreBar } from '../../ui/ScoreBar'
import { LobGroupCard } from './LobGroupCard'
import type { GroupedRoleMappingsResponse, RoleMappingCompact, OnetSearchResult } from '../../../services/discoveryApi'

export interface GroupedRoleMappingsViewProps {
  data: GroupedRoleMappingsResponse
  onBulkConfirmLob: (lob: string, threshold: number) => void
  onBulkConfirmAll: (threshold: number) => void
  onConfirmMapping: (mappingId: string) => void
  onRemapMapping: (mappingId: string, onetCode: string, onetTitle: string) => void
  isConfirming?: boolean
  // O*NET search support
  activeRemapId?: string | null
  onSetActiveRemapId?: (id: string | null) => void
  searchQuery?: string
  onSearchQueryChange?: (query: string) => void
  searchResults?: OnetSearchResult[]
  isSearching?: boolean
}

export function GroupedRoleMappingsView({
  data,
  onBulkConfirmLob,
  onBulkConfirmAll,
  onConfirmMapping,
  onRemapMapping,
  isConfirming = false,
  activeRemapId,
  onSetActiveRemapId,
  searchQuery = '',
  onSearchQueryChange,
  searchResults = [],
  isSearching = false,
}: GroupedRoleMappingsViewProps) {
  const { overall_summary, lob_groups, ungrouped_mappings } = data

  // Track which LOB groups are expanded (persists across data updates)
  const [expandedLobs, setExpandedLobs] = useState<Set<string>>(new Set())

  const toggleLobExpanded = useCallback((lob: string) => {
    setExpandedLobs((prev) => {
      const next = new Set(prev)
      if (next.has(lob)) {
        next.delete(lob)
      } else {
        next.add(lob)
      }
      return next
    })
  }, [])

  const confirmationRate = overall_summary.total_roles > 0
    ? overall_summary.confirmed_count / overall_summary.total_roles
    : 0

  const allConfirmed = overall_summary.confirmed_count === overall_summary.total_roles

  return (
    <div className="space-y-6">
      {/* Overall summary card */}
      <div className="surface p-5 rounded-lg">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-display font-semibold text-default">Role Mapping Summary</h2>
            <p className="text-sm text-muted">
              {overall_summary.total_roles} unique roles across {overall_summary.total_employees.toLocaleString()} employees
            </p>
          </div>
          {!allConfirmed && overall_summary.pending_count > 0 && (
            <Button
              variant="primary"
              icon={<IconCheck size={16} />}
              onClick={() => onBulkConfirmAll(0.85)}
              disabled={isConfirming}
            >
              {isConfirming ? 'Confirming...' : 'Confirm all high-confidence'}
            </Button>
          )}
        </div>

        {/* Progress bar */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm text-muted">Confirmation Progress</span>
            <span className="text-sm font-medium text-default">
              {overall_summary.confirmed_count} / {overall_summary.total_roles}
            </span>
          </div>
          <ScoreBar value={confirmationRate} variant="success" size="lg" />
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-4 gap-4">
          <StatCard
            label="Total Roles"
            value={overall_summary.total_roles}
            icon={<IconUsers size={16} />}
          />
          <StatCard
            label="Confirmed"
            value={overall_summary.confirmed_count}
            variant="success"
          />
          <StatCard
            label="Pending"
            value={overall_summary.pending_count}
            variant="warning"
          />
          <StatCard
            label="Needs Review"
            value={overall_summary.low_confidence_count}
            variant="error"
          />
        </div>
      </div>

      {/* LOB groups */}
      {lob_groups.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-muted uppercase tracking-wide">
            By Line of Business ({lob_groups.length})
          </h3>
          {lob_groups.map((group) => (
            <LobGroupCard
              key={group.lob}
              group={group}
              isExpanded={expandedLobs.has(group.lob)}
              onToggleExpanded={() => toggleLobExpanded(group.lob)}
              onBulkConfirm={onBulkConfirmLob}
              onConfirmMapping={onConfirmMapping}
              onRemapMapping={onRemapMapping}
              isConfirming={isConfirming}
              activeRemapId={activeRemapId}
              onSetActiveRemapId={onSetActiveRemapId}
              searchQuery={searchQuery}
              onSearchQueryChange={onSearchQueryChange}
              searchResults={searchResults}
              isSearching={isSearching}
            />
          ))}
        </div>
      )}

      {/* Ungrouped mappings */}
      {ungrouped_mappings.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-muted uppercase tracking-wide">
            Ungrouped Roles ({ungrouped_mappings.length})
          </h3>
          <div className="surface rounded-lg divide-y divide-border">
            {ungrouped_mappings.map((mapping) => (
              <UngroupedMappingRow
                key={mapping.id}
                mapping={mapping}
                onConfirm={() => onConfirmMapping(mapping.id)}
                onRemap={(onetCode, onetTitle) => onRemapMapping(mapping.id, onetCode, onetTitle)}
                isRemapActive={activeRemapId === mapping.id}
                onSetRemapActive={(active) => onSetActiveRemapId?.(active ? mapping.id : null)}
                searchQuery={activeRemapId === mapping.id ? searchQuery : ''}
                onSearchQueryChange={onSearchQueryChange}
                searchResults={activeRemapId === mapping.id ? searchResults : []}
                isSearching={isSearching}
              />
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {lob_groups.length === 0 && ungrouped_mappings.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted">No role mappings found.</p>
        </div>
      )}
    </div>
  )
}

interface StatCardProps {
  label: string
  value: number
  icon?: React.ReactNode
  variant?: 'default' | 'success' | 'warning' | 'error'
}

function StatCard({ label, value, icon, variant = 'default' }: StatCardProps) {
  const variantClasses = {
    default: 'text-default',
    success: 'text-success',
    warning: 'text-warning',
    error: 'text-error',
  }

  return (
    <div className="p-3 bg-bg-muted rounded-lg">
      <div className="flex items-center gap-2 mb-1">
        {icon && <span className="text-muted">{icon}</span>}
        <span className="text-xs text-muted uppercase tracking-wide">{label}</span>
      </div>
      <p className={`text-2xl font-bold ${variantClasses[variant]}`}>{value}</p>
    </div>
  )
}

interface UngroupedMappingRowProps {
  mapping: RoleMappingCompact
  onConfirm: () => void
  onRemap: (onetCode: string, onetTitle: string) => void
  isRemapActive?: boolean
  onSetRemapActive?: (active: boolean) => void
  searchQuery?: string
  onSearchQueryChange?: (query: string) => void
  searchResults?: OnetSearchResult[]
  isSearching?: boolean
}

function UngroupedMappingRow({
  mapping,
  onConfirm,
  onRemap,
  isRemapActive = false,
  onSetRemapActive,
  searchQuery = '',
  onSearchQueryChange,
  searchResults = [],
  isSearching = false,
}: UngroupedMappingRowProps) {
  const confidencePercent = Math.round(mapping.confidence_score * 100)
  const isLowConfidence = mapping.confidence_score < 0.6

  return (
    <div
      className={`p-4 ${
        mapping.is_confirmed ? 'bg-success/5' : ''
      }`}
    >
      {/* Header with role info and stats */}
      <div className="flex items-start gap-4 mb-3">
        {/* Source role - labeled clearly */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs text-muted uppercase tracking-wide">Your Role</span>
            {mapping.is_confirmed && (
              <span className="inline-flex items-center rounded-full bg-success/15 px-2 py-0.5 text-xs font-medium text-success">
                Confirmed
              </span>
            )}
          </div>
          <p className="font-display font-medium text-default truncate">
            {mapping.source_role}
          </p>
        </div>

        {/* Stats */}
        <div className="flex items-center gap-4 shrink-0">
          {/* Employee count */}
          <div className="flex items-center gap-1 text-muted">
            <IconUsers size={14} />
            <span className="text-sm">{mapping.employee_count}</span>
          </div>

          {/* Confidence */}
          <div className={`text-sm font-medium ${isLowConfidence ? 'text-warning' : 'text-muted'}`}>
            {confidencePercent}%
          </div>
        </div>
      </div>

      {/* O*NET mapping section */}
      {isRemapActive ? (
        /* Remap search mode */
        <div className="bg-bg-muted rounded-lg p-3">
          <p className="text-xs text-muted uppercase tracking-wide mb-2">Search O*NET Occupations</p>
          <div className="relative mb-3">
            <IconSearch
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-muted"
            />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => onSearchQueryChange?.(e.target.value)}
              placeholder="Type to search O*NET occupations..."
              className="input pl-9 w-full"
              autoFocus
            />
          </div>

          {/* Search results */}
          {searchQuery && (
            <div className="space-y-1 max-h-48 overflow-y-auto mb-3">
              {isSearching ? (
                <p className="text-sm text-muted p-2">Searching...</p>
              ) : searchResults.length === 0 ? (
                <p className="text-sm text-muted p-2">No results found</p>
              ) : (
                searchResults.map((result) => (
                  <button
                    key={result.code}
                    onClick={() => {
                      onRemap(result.code, result.title)
                      onSetRemapActive?.(false)
                    }}
                    className="
                      w-full text-left p-2 rounded-md
                      hover:bg-elevated transition-colors
                    "
                  >
                    <p className="text-sm font-medium text-default">
                      {result.title}
                    </p>
                    <p className="text-xs text-muted">{result.code}</p>
                  </button>
                ))
              )}
            </div>
          )}

          <div className="flex justify-end">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onSetRemapActive?.(false)}
            >
              Cancel
            </Button>
          </div>
        </div>
      ) : (
        /* Display mapped O*NET */
        <div className="flex items-center justify-between gap-4 p-3 bg-bg-muted rounded-lg">
          <div className="min-w-0">
            <p className="text-xs text-muted uppercase tracking-wide mb-0.5">
              O*NET Match
            </p>
            <p className="text-sm font-medium text-default truncate">
              {mapping.onet_title || 'No mapping'}
            </p>
            {mapping.onet_code && (
              <p className="text-xs text-muted">{mapping.onet_code}</p>
            )}
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Button
              variant="ghost"
              size="sm"
              icon={<IconRefresh size={14} />}
              onClick={() => onSetRemapActive?.(true)}
            >
              Remap
            </Button>
            {!mapping.is_confirmed && (
              <Button variant="primary" size="sm" icon={<IconCheck size={14} />} onClick={onConfirm}>
                Confirm
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
