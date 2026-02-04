import { useState, useMemo } from 'react'
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
} from '../../components/ui/Icons'
import { useAnalysisResults, Dimension, PriorityTier } from '../../hooks/useAnalysisResults'

const DIMENSIONS: { key: Dimension; label: string }[] = [
  { key: 'ROLE', label: 'By Role' },
  { key: 'DEPARTMENT', label: 'By Department' },
  { key: 'GEOGRAPHY', label: 'By Geography' },
  { key: 'TASK', label: 'By Task' },
  { key: 'LOB', label: 'By Line of Business' },
]

const TIERS: { key: PriorityTier | 'ALL'; label: string }[] = [
  { key: 'ALL', label: 'All' },
  { key: 'HIGH', label: 'High' },
  { key: 'MEDIUM', label: 'Medium' },
  { key: 'LOW', label: 'Low' },
]

type SortKey = 'name' | 'exposure' | 'impact' | 'priority'
type SortDir = 'asc' | 'desc'

export function AnalysisStep() {
  const { sessionId } = useParams()
  const [activeDimension, setActiveDimension] = useState<Dimension>('ROLE')
  const [activeTier, setActiveTier] = useState<PriorityTier | 'ALL'>('ALL')
  const [sortKey, setSortKey] = useState<SortKey>('priority')
  const [sortDir, setSortDir] = useState<SortDir>('desc')

  const {
    results,
    isLoading,
    error,
    triggerAnalysis,
    isTriggering,
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
      }
      return sortDir === 'asc' ? comparison : -comparison
    })
  }, [results, sortKey, sortDir])

  // Summary stats
  const stats = useMemo(() => {
    if (!results || results.length === 0) {
      return { total: 0, highCount: 0, avgExposure: 0, avgPriority: 0 }
    }

    const highCount = results.filter((r) => r.tier === 'HIGH').length
    const avgExposure = results.reduce((sum, r) => sum + r.exposure, 0) / results.length
    const avgPriority = results.reduce((sum, r) => sum + r.priority, 0) / results.length

    return {
      total: results.length,
      highCount,
      avgExposure,
      avgPriority,
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
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="surface p-4 text-center">
              <p className="text-2xl font-display font-bold text-default">
                {stats.total}
              </p>
              <p className="text-xs text-muted">Total Items</p>
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
                onClick={() => setActiveDimension(dim.key)}
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
                    {sortedResults.map((result, index) => (
                      <tr
                        key={result.id}
                        className="border-b border-border last:border-0 hover:bg-bg-muted/30 transition-colors animate-fade-in"
                        style={{ animationDelay: `${Math.min(index, 15) * 30}ms` }}
                      >
                        <td className="p-4">
                          <span className="font-medium text-default">
                            {result.name}
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
                    ))}
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
