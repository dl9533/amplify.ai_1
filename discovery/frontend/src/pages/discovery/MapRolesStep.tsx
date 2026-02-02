import { useState, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import { AppShell } from '../../components/layout/AppShell'
import { DiscoveryWizard, StepContent } from '../../components/layout/DiscoveryWizard'
import { Button } from '../../components/ui/Button'
import { ConfidenceBadge } from '../../components/ui/Badge'
import { LoadingState, ErrorState } from '../../components/ui/EmptyState'
import {
  IconCheck,
  IconSearch,
  IconRefresh,
  IconCheckCircle,
} from '../../components/ui/Icons'
import { useRoleMappings } from '../../hooks/useRoleMappings'
import { useOnetSearch } from '../../hooks/useOnetSearch'

export function MapRolesStep() {
  const { sessionId } = useParams()
  const {
    mappings,
    isLoading,
    error,
    confirmMapping,
    bulkConfirm,
    remapRole,
  } = useRoleMappings(sessionId || '')

  const [searchQuery, setSearchQuery] = useState('')
  const [activeRemapId, setActiveRemapId] = useState<string | null>(null)

  // O*NET search for remapping
  const { results: searchResults, isSearching } = useOnetSearch(
    activeRemapId ? searchQuery : ''
  )

  // Count confirmed/total
  const confirmedCount = mappings.filter((m) => m.confirmed).length
  const totalCount = mappings.length
  const allConfirmed = confirmedCount === totalCount && totalCount > 0

  // Group by confidence level
  const groupedMappings = useMemo(() => {
    const highConfidence = mappings.filter((m) => m.confidence >= 0.85)
    const mediumConfidence = mappings.filter((m) => m.confidence >= 0.6 && m.confidence < 0.85)
    const lowConfidence = mappings.filter((m) => m.confidence < 0.6)
    return { highConfidence, mediumConfidence, lowConfidence }
  }, [mappings])

  const handleBulkConfirm = async (threshold: number) => {
    await bulkConfirm(threshold)
  }

  const handleRemap = async (mappingId: string, onetCode: string, onetTitle: string) => {
    await remapRole(mappingId, onetCode, onetTitle)
    setActiveRemapId(null)
    setSearchQuery('')
  }

  if (isLoading) {
    return (
      <AppShell>
        <DiscoveryWizard currentStep={2}>
          <LoadingState message="Loading role mappings..." />
        </DiscoveryWizard>
      </AppShell>
    )
  }

  if (error) {
    return (
      <AppShell>
        <DiscoveryWizard currentStep={2}>
          <ErrorState message={error} />
        </DiscoveryWizard>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <DiscoveryWizard currentStep={2} canProceed={allConfirmed}>
        <StepContent
          title="Map Roles to O*NET"
          description="Review and confirm the O*NET occupation matches for each role."
          actions={
            <div className="flex items-center gap-2">
              {groupedMappings.highConfidence.length > 0 && (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => handleBulkConfirm(0.85)}
                >
                  Confirm all {'>'}85%
                </Button>
              )}
            </div>
          }
        >
          {/* Progress indicator */}
          <div className="surface p-4 mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-muted">Mapping Progress</span>
              <span className="text-sm font-medium text-default">
                {confirmedCount} / {totalCount} confirmed
              </span>
            </div>
            <div className="h-2 bg-bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-success rounded-full transition-all duration-500"
                style={{ width: `${totalCount > 0 ? (confirmedCount / totalCount) * 100 : 0}%` }}
              />
            </div>
          </div>

          {/* Mappings list */}
          <div className="space-y-3">
            {mappings.map((mapping, index) => (
              <div
                key={mapping.id}
                className={`
                  surface p-4
                  animate-slide-up
                  ${mapping.confirmed ? 'border-success/30 bg-success/5' : ''}
                `}
                style={{ animationDelay: `${Math.min(index, 10) * 30}ms` }}
              >
                <div className="flex items-start gap-4">
                  {/* Status indicator */}
                  <div
                    className={`
                      w-10 h-10 rounded-lg flex items-center justify-center shrink-0
                      ${mapping.confirmed ? 'bg-success/15 text-success' : 'bg-bg-muted text-subtle'}
                    `}
                  >
                    {mapping.confirmed ? (
                      <IconCheckCircle size={20} />
                    ) : (
                      <span className="text-sm font-medium">{index + 1}</span>
                    )}
                  </div>

                  {/* Mapping content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-4 mb-2">
                      {/* Source role */}
                      <div>
                        <p className="text-xs text-muted uppercase tracking-wide mb-0.5">
                          Your Role
                        </p>
                        <p className="font-display font-medium text-default">
                          {mapping.roleName}
                        </p>
                      </div>

                      {/* Confidence badge */}
                      <ConfidenceBadge score={mapping.confidence} />
                    </div>

                    {/* O*NET mapping */}
                    {activeRemapId === mapping.id ? (
                      /* Remap search mode */
                      <div className="mt-3">
                        <div className="relative mb-3">
                          <IconSearch
                            size={16}
                            className="absolute left-3 top-1/2 -translate-y-1/2 text-muted"
                          />
                          <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search O*NET occupations..."
                            className="input pl-9"
                            autoFocus
                          />
                        </div>

                        {/* Search results */}
                        {searchQuery && (
                          <div className="space-y-1 max-h-48 overflow-y-auto">
                            {isSearching ? (
                              <p className="text-sm text-muted p-2">Searching...</p>
                            ) : searchResults.length === 0 ? (
                              <p className="text-sm text-muted p-2">No results found</p>
                            ) : (
                              searchResults.map((result) => (
                                <button
                                  key={result.code}
                                  onClick={() => handleRemap(mapping.id, result.code, result.title)}
                                  className="
                                    w-full text-left p-2 rounded-md
                                    hover:bg-bg-muted transition-colors
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

                        <div className="mt-3 flex justify-end">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setActiveRemapId(null)
                              setSearchQuery('')
                            }}
                          >
                            Cancel
                          </Button>
                        </div>
                      </div>
                    ) : (
                      /* Display mapped O*NET */
                      <div className="flex items-center justify-between gap-4 mt-3 p-3 bg-bg-muted rounded-lg">
                        <div className="min-w-0">
                          <p className="text-xs text-muted uppercase tracking-wide mb-0.5">
                            O*NET Match
                          </p>
                          <p className="text-sm font-medium text-default truncate">
                            {mapping.onetTitle}
                          </p>
                          <p className="text-xs text-muted">{mapping.onetCode}</p>
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                          <Button
                            variant="ghost"
                            size="sm"
                            icon={<IconRefresh size={14} />}
                            onClick={() => setActiveRemapId(mapping.id)}
                          >
                            Remap
                          </Button>
                          {!mapping.confirmed && (
                            <Button
                              variant="primary"
                              size="sm"
                              icon={<IconCheck size={14} />}
                              onClick={() => confirmMapping(mapping.id)}
                            >
                              Confirm
                            </Button>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Empty state */}
          {mappings.length === 0 && (
            <div className="text-center py-12">
              <p className="text-muted">No roles found. Please upload workforce data first.</p>
            </div>
          )}
        </StepContent>
      </DiscoveryWizard>
    </AppShell>
  )
}
