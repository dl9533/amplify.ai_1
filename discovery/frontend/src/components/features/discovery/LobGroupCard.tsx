import { useState } from 'react'
import { Button } from '../../ui/Button'
import { IconChevronDown, IconChevronRight, IconCheck, IconUsers } from '../../ui/Icons'
import { ScoreBar } from '../../ui/ScoreBar'
import type { LobGroup, RoleMappingCompact } from '../../../services/discoveryApi'

export interface LobGroupCardProps {
  group: LobGroup
  onBulkConfirm: (lob: string, threshold: number) => void
  onConfirmMapping: (mappingId: string) => void
  onRemapMapping: (mappingId: string) => void
  isConfirming?: boolean
}

export function LobGroupCard({
  group,
  onBulkConfirm,
  onConfirmMapping,
  onRemapMapping,
  isConfirming = false,
}: LobGroupCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const { summary, mappings, lob } = group

  const confirmationRate = summary.total_roles > 0
    ? (summary.confirmed_count / summary.total_roles) * 100
    : 0

  const unconfirmedHighConfidence = mappings.filter(
    (m) => !m.is_confirmed && m.confidence_score >= 0.85
  ).length

  return (
    <div className="surface rounded-lg overflow-hidden">
      {/* Header - always visible */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 flex items-center justify-between hover:bg-bg-muted/50 transition-colors"
        aria-expanded={isExpanded}
        aria-controls={`lob-group-${lob}`}
      >
        <div className="flex items-center gap-3">
          <span className="text-muted">
            {isExpanded ? <IconChevronDown size={20} /> : <IconChevronRight size={20} />}
          </span>
          <div className="text-left">
            <h3 className="font-display font-semibold text-default">{lob}</h3>
            <p className="text-sm text-muted">
              {summary.total_roles} roles · {summary.total_employees.toLocaleString()} employees
            </p>
          </div>
        </div>

        {/* Summary stats */}
        <div className="flex items-center gap-6">
          <div className="text-right">
            <p className="text-sm font-medium text-default">
              {summary.confirmed_count}/{summary.total_roles}
            </p>
            <p className="text-xs text-muted">confirmed</p>
          </div>
          <div className="w-24">
            <ScoreBar value={confirmationRate} max={100} variant="success" />
          </div>
          {summary.low_confidence_count > 0 && (
            <div className="text-right">
              <p className="text-sm font-medium text-warning">{summary.low_confidence_count}</p>
              <p className="text-xs text-muted">needs review</p>
            </div>
          )}
        </div>
      </button>

      {/* Expanded content */}
      {isExpanded && (
        <div id={`lob-group-${lob}`} className="border-t border-border">
          {/* Bulk actions */}
          {summary.pending_count > 0 && (
            <div className="p-3 bg-bg-muted/50 flex items-center justify-between">
              <span className="text-sm text-muted">
                {summary.pending_count} pending confirmation
              </span>
              {unconfirmedHighConfidence > 0 && (
                <Button
                  variant="secondary"
                  size="sm"
                  icon={<IconCheck size={14} />}
                  onClick={() => onBulkConfirm(lob, 0.85)}
                  disabled={isConfirming}
                >
                  {isConfirming ? 'Confirming...' : `Confirm ${unconfirmedHighConfidence} high-confidence`}
                </Button>
              )}
            </div>
          )}

          {/* Mappings list */}
          <div className="divide-y divide-border">
            {mappings.map((mapping) => (
              <LobMappingRow
                key={mapping.id}
                mapping={mapping}
                onConfirm={() => onConfirmMapping(mapping.id)}
                onRemap={() => onRemapMapping(mapping.id)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

interface LobMappingRowProps {
  mapping: RoleMappingCompact
  onConfirm: () => void
  onRemap: () => void
}

function LobMappingRow({ mapping, onConfirm, onRemap }: LobMappingRowProps) {
  const confidencePercent = Math.round(mapping.confidence_score * 100)
  const isLowConfidence = mapping.confidence_score < 0.6

  return (
    <div
      className={`p-3 flex items-center gap-4 ${
        mapping.is_confirmed ? 'bg-success/5' : ''
      }`}
    >
      {/* Role info */}
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

      {/* Employee count */}
      <div className="flex items-center gap-1 text-muted">
        <IconUsers size={14} />
        <span className="text-sm">{mapping.employee_count}</span>
      </div>

      {/* Confidence */}
      <div className={`text-sm font-medium ${isLowConfidence ? 'text-warning' : 'text-muted'}`}>
        {confidencePercent}%
      </div>

      {/* Actions */}
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
