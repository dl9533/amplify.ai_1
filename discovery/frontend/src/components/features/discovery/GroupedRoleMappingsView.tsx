import { Button } from '../../ui/Button'
import { IconCheck, IconUsers } from '../../ui/Icons'
import { ScoreBar } from '../../ui/ScoreBar'
import { LobGroupCard } from './LobGroupCard'
import type { GroupedRoleMappingsResponse, RoleMappingCompact } from '../../../services/discoveryApi'

export interface GroupedRoleMappingsViewProps {
  data: GroupedRoleMappingsResponse
  onBulkConfirmLob: (lob: string, threshold: number) => void
  onBulkConfirmAll: (threshold: number) => void
  onConfirmMapping: (mappingId: string) => void
  onRemapMapping: (mappingId: string) => void
  isConfirming?: boolean
}

export function GroupedRoleMappingsView({
  data,
  onBulkConfirmLob,
  onBulkConfirmAll,
  onConfirmMapping,
  onRemapMapping,
  isConfirming = false,
}: GroupedRoleMappingsViewProps) {
  const { overall_summary, lob_groups, ungrouped_mappings } = data

  const confirmationRate = overall_summary.total_roles > 0
    ? (overall_summary.confirmed_count / overall_summary.total_roles) * 100
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
          <ScoreBar value={confirmationRate} max={100} variant="success" size="lg" />
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
              onBulkConfirm={onBulkConfirmLob}
              onConfirmMapping={onConfirmMapping}
              onRemapMapping={onRemapMapping}
              isConfirming={isConfirming}
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
                onRemap={() => onRemapMapping(mapping.id)}
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
  onRemap: () => void
}

function UngroupedMappingRow({ mapping, onConfirm, onRemap }: UngroupedMappingRowProps) {
  const confidencePercent = Math.round(mapping.confidence_score * 100)
  const isLowConfidence = mapping.confidence_score < 0.6

  return (
    <div
      className={`p-3 flex items-center gap-4 ${
        mapping.is_confirmed ? 'bg-success/5' : ''
      }`}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="font-medium text-default truncate">{mapping.source_role}</p>
          {mapping.is_confirmed && (
            <span className="inline-flex items-center rounded-full bg-success/15 px-2 py-0.5 text-xs font-medium text-success">
              Confirmed
            </span>
          )}
        </div>
        <p className="text-sm text-muted truncate">
          → {mapping.onet_title || 'No mapping'}
          {mapping.onet_code && <span className="ml-1 text-xs">({mapping.onet_code})</span>}
        </p>
      </div>

      <div className="flex items-center gap-1 text-muted">
        <IconUsers size={14} />
        <span className="text-sm">{mapping.employee_count}</span>
      </div>

      <div className={`text-sm font-medium ${isLowConfidence ? 'text-warning' : 'text-muted'}`}>
        {confidencePercent}%
      </div>

      <div className="flex items-center gap-2">
        {!mapping.is_confirmed && (
          <Button variant="primary" size="sm" onClick={onConfirm}>
            Confirm
          </Button>
        )}
        <Button variant="ghost" size="sm" onClick={onRemap}>
          Remap
        </Button>
      </div>
    </div>
  )
}
