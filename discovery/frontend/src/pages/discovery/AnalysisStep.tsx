import { useState, useMemo, Fragment } from 'react'
import { useParams } from 'react-router-dom'
import { AppShell } from '../../components/layout/AppShell'
import { DiscoveryWizard, StepContent } from '../../components/layout/DiscoveryWizard'
import { Button } from '../../components/ui/Button'
import { TierBadge } from '../../components/ui/Badge'
import { MiniBar } from '../../components/ui/ScoreBar'
import { LoadingState, ErrorState, EmptyState } from '../../components/ui/EmptyState'
import {
  IconRefresh,
  IconBarChart,
  IconChevronUp,
  IconChevronDown,
  IconChevronRight,
  IconAlertCircle,
  IconX,
} from '../../components/ui/Icons'
import { useAnalysisResults, Dimension, PriorityTier } from '../../hooks/useAnalysisResults'
import { RoleTaskBreakdown } from '../../components/features/discovery/RoleTaskBreakdown'

const DIMENSIONS: { key: Dimension; label: string; entityLabel: string }[] = [
  { key: 'role', label: 'By Role', entityLabel: 'Roles' },
  { key: 'department', label: 'By Department', entityLabel: 'Departments' },
  { key: 'geography', label: 'By Geography', entityLabel: 'Locations' },
  { key: 'lob', label: 'By Line of Business', entityLabel: 'Lines of Business' },
]

const TIERS: { key: PriorityTier | 'ALL'; label: string }[] = [
  { key: 'ALL', label: 'All' },
  { key: 'HIGH', label: 'High' },
  { key: 'MEDIUM', label: 'Medium' },
  { key: 'LOW', label: 'Low' },
]

type SortKey = 'name' | 'exposure' | 'impact' | 'priority' | 'rowCount'
type SortDir = 'asc' | 'desc'

export function AnalysisStep() {
  const { sessionId } = useParams()
  const [activeDimension, setActiveDimension] = useState<Dimension>('role')
  const [activeTier, setActiveTier] = useState<PriorityTier | 'ALL'>('ALL')
  const [sortKey, setSortKey] = useState<SortKey>('priority')
  const [sortDir, setSortDir] = useState<SortDir>('desc')
  const [expandedRowId, setExpandedRowId] = useState<string | null>(null)

  const {
    results,
    isLoading,
    error,
    warnings,
    triggerAnalysis,
    isTriggering,
    clearWarnings,
  } = useAnalysisResults(
    sessionId || '',
    activeDimension,
    activeTier === 'ALL' ? undefined : activeTier
  )

  // Sort results
  const sortedResults = useMemo(() => {
    if (!results) return []

    return [...results].sort((a, b) => {
      let comparison = 0
      switch (sortKey) {
        case 'name':
          comparison = a.name.localeCompare(b.name)
          break
        case 'exposure':
          comparison = a.exposure - b.exposure
          break
        case 'impact':
          comparison = a.impact - b.impact
          break
        case 'priority':
          comparison = a.priority - b.priority
          break
        case 'rowCount':
          comparison = (a.rowCount ?? 0) - (b.rowCount ?? 0)
          break
      }
      return sortDir === 'asc' ? comparison : -comparison
    })
  }, [results, sortKey, sortDir])

  // Summary stats
  const stats = useMemo(() => {
    if (!results || results.length === 0) {
      return { total: 0, highCount: 0, avgExposure: 0, avgPriority: 0, totalEmployees: 0 }
    }

    const highCount = results.filter((r) => r.tier === 'HIGH').length
    const avgExposure = results.reduce((sum, r) => sum + r.exposure, 0) / results.length
    const avgPriority = results.reduce((sum, r) => sum + r.priority, 0) / results.length
    const totalEmployees = results.reduce((sum, r) => sum + (r.rowCount ?? 0), 0)

    return {
      total: results.length,
      highCount,
      avgExposure,
      avgPriority,
      totalEmployees,
    }
  }, [results])

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  const SortIcon = ({ column }: { column: SortKey }) => {
    if (sortKey !== column) return null
    return sortDir === 'asc' ? (
      <IconChevronUp size={14} />
    ) : (
      <IconChevronDown size={14} />
    )
  }

  const handleRowClick = (resultId: string, roleMappingId?: string) => {
    // Only allow expansion for role dimension with a valid roleMappingId
    if (activeDimension !== 'role' || !roleMappingId) return
    setExpandedRowId(expandedRowId === resultId ? null : resultId)
  }

  // Collapse expanded row when switching dimensions
  const handleDimensionChange = (dim: Dimension) => {
    setActiveDimension(dim)
    setExpandedRowId(null)
  }

  const canProceed = results && results.length > 0

  return (
    <AppShell>
      <DiscoveryWizard currentStep={4} canProceed={canProceed}>
        <StepContent
          title="Analysis Results"
          description="Review automation potential scores across different dimensions."
          actions={
            <Button
              variant="secondary"
              size="sm"
              icon={<IconRefresh size={16} />}
              onClick={triggerAnalysis}
              loading={isTriggering}
            >
              Re-analyze
            </Button>
          }
        >
          {/* Summary stats */}
          <div className="grid grid-cols-5 gap-4 mb-6">
            <div className="surface p-4 text-center">
              <p className="text-2xl font-display font-bold text-default">
                {stats.total}
              </p>
              <p className="text-xs text-muted">
                Total {DIMENSIONS.find((d) => d.key === activeDimension)?.entityLabel ?? 'Entities'}
              </p>
            </div>
            <div className="surface p-4 text-center">
              <p className="text-2xl font-display font-bold text-default">
                {stats.totalEmployees.toLocaleString()}
              </p>
              <p className="text-xs text-muted">Total Employees</p>
            </div>
            <div className="surface p-4 text-center">
              <p className="text-2xl font-display font-bold text-success">
                {stats.highCount}
              </p>
              <p className="text-xs text-muted">High Priority</p>
            </div>
            <div className="surface p-4 text-center">
              <p className="text-2xl font-display font-bold text-accent">
                {Math.round(stats.avgExposure * 100)}%
              </p>
              <p className="text-xs text-muted">Avg Exposure</p>
            </div>
            <div className="surface p-4 text-center">
              <p className="text-2xl font-display font-bold text-warning">
                {Math.round(stats.avgPriority * 100)}%
              </p>
              <p className="text-xs text-muted">Avg Priority</p>
            </div>
          </div>

          {/* Dimension tabs */}
          <div className="flex items-center gap-2 mb-4 overflow-x-auto pb-2">
            {DIMENSIONS.map((dim) => (
              <button
                key={dim.key}
                onClick={() => handleDimensionChange(dim.key)}
                className={activeDimension === dim.key ? 'tab-active' : 'tab'}
              >
                {dim.label}
              </button>
            ))}
          </div>

          {/* Tier filter */}
          <div className="flex items-center gap-2 mb-6">
            <span className="text-sm text-muted">Filter:</span>
            {TIERS.map((tier) => (
              <button
                key={tier.key}
                onClick={() => setActiveTier(tier.key)}
                className={`
                  px-3 py-1 text-sm rounded-full border transition-all
                  ${
                    activeTier === tier.key
                      ? 'bg-accent/15 border-accent/30 text-accent'
                      : 'border-border text-muted hover:text-default hover:border-border-accent/30'
                  }
                `}
              >
                {tier.label}
              </button>
            ))}
          </div>

          {/* Warnings display */}
          {warnings && warnings.length > 0 && (
            <div className="mb-6 p-4 border border-warning/30 bg-warning/5 rounded-lg">
              <div className="flex items-start gap-3">
                <IconAlertCircle size={20} className="text-warning shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="font-medium text-warning mb-1">Warnings</p>
                  <ul className="text-sm text-muted space-y-1">
                    {warnings.map((warning, index) => (
                      <li key={index}>{warning}</li>
                    ))}
                  </ul>
                </div>
                <button
                  onClick={clearWarnings}
                  className="text-muted hover:text-default transition-colors"
                  aria-label="Dismiss warnings"
                >
                  <IconX size={16} />
                </button>
              </div>
            </div>
          )}

          {/* Results table */}
          {isLoading ? (
            <LoadingState message="Loading analysis..." />
          ) : error ? (
            <ErrorState message={error} />
          ) : sortedResults.length === 0 ? (
            <EmptyState
              icon={<IconBarChart size={28} />}
              title="No results yet"
              description="Run the analysis to see automation scores for your workforce."
              action={
                <Button
                  variant="primary"
                  size="sm"
                  icon={<IconRefresh size={16} />}
                  onClick={triggerAnalysis}
                  loading={isTriggering}
                >
                  Run Analysis
                </Button>
              }
            />
          ) : (
            <div className="surface overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-border bg-bg-muted/50">
                      <th className="text-left p-4">
                        <button
                          onClick={() => handleSort('name')}
                          className="flex items-center gap-1 text-xs font-medium text-muted uppercase tracking-wide hover:text-default"
                        >
                          Name
                          <SortIcon column="name" />
                        </button>
                      </th>
                      <th className="text-left p-4">
                        <button
                          onClick={() => handleSort('rowCount')}
                          className="flex items-center gap-1 text-xs font-medium text-muted uppercase tracking-wide hover:text-default"
                        >
                          Employees
                          <SortIcon column="rowCount" />
                        </button>
                      </th>
                      <th className="text-left p-4">
                        <button
                          onClick={() => handleSort('exposure')}
                          className="flex items-center gap-1 text-xs font-medium text-muted uppercase tracking-wide hover:text-default"
                        >
                          AI Exposure
                          <SortIcon column="exposure" />
                        </button>
                      </th>
                      <th className="text-left p-4">
                        <button
                          onClick={() => handleSort('impact')}
                          className="flex items-center gap-1 text-xs font-medium text-muted uppercase tracking-wide hover:text-default"
                        >
                          Impact
                          <SortIcon column="impact" />
                        </button>
                      </th>
                      <th className="text-left p-4">
                        <button
                          onClick={() => handleSort('priority')}
                          className="flex items-center gap-1 text-xs font-medium text-muted uppercase tracking-wide hover:text-default"
                        >
                          Priority
                          <SortIcon column="priority" />
                        </button>
                      </th>
                      <th className="text-left p-4">
                        <span className="text-xs font-medium text-muted uppercase tracking-wide">
                          Tier
                        </span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedResults.map((result, index) => {
                      const isExpandable = activeDimension === 'role' && !!result.roleMappingId
                      const isExpanded = expandedRowId === result.id

                      return (
                        <Fragment key={result.id}>
                          <tr
                            onClick={() => handleRowClick(result.id, result.roleMappingId)}
                            className={`
                              border-b border-border transition-colors animate-fade-in
                              ${isExpandable ? 'cursor-pointer hover:bg-bg-muted/30' : ''}
                              ${isExpanded ? 'bg-bg-muted/20' : ''}
                            `}
                            style={{ animationDelay: `${Math.min(index, 15) * 30}ms` }}
                          >
                            <td className="p-4">
                              <div className="flex items-center gap-2">
                                {isExpandable && (
                                  <span className="text-muted shrink-0">
                                    {isExpanded ? (
                                      <IconChevronDown size={16} />
                                    ) : (
                                      <IconChevronRight size={16} />
                                    )}
                                  </span>
                                )}
                                <span className="font-medium text-default">
                                  {result.name}
                                </span>
                              </div>
                            </td>
                            <td className="p-4">
                              <span className="text-default tabular-nums">
                                {result.rowCount ?? '-'}
                              </span>
                            </td>
                            <td className="p-4">
                              <MiniBar value={result.exposure} />
                            </td>
                            <td className="p-4">
                              <MiniBar value={result.impact} />
                            </td>
                            <td className="p-4">
                              <MiniBar value={result.priority} />
                            </td>
                            <td className="p-4">
                              <TierBadge tier={result.tier} />
                            </td>
                          </tr>
                          {isExpanded && result.roleMappingId && sessionId && (
                            <tr>
                              <td colSpan={6} className="p-0">
                                <RoleTaskBreakdown
                                  sessionId={sessionId}
                                  roleMappingId={result.roleMappingId}
                                />
                              </td>
                            </tr>
                          )}
                        </Fragment>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </StepContent>
      </DiscoveryWizard>
    </AppShell>
  )
}
