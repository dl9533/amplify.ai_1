import { useState } from 'react'
import { AppShell, PageContainer, PageHeader } from '../../components/layout/AppShell'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { LoadingState } from '../../components/ui/EmptyState'
import { IconRefresh, IconCheck, IconDatabase } from '../../components/ui/Icons'
import { useOnetSync } from '../../hooks/useOnetSync'

export function AdminPage() {
  const {
    status,
    isLoading,
    isSyncing,
    error,
    syncResult,
    triggerSync,
    refresh,
  } = useOnetSync()

  const [syncVersion, setSyncVersion] = useState('30_1')
  const [syncError, setSyncError] = useState<string | null>(null)

  const handleSync = async () => {
    try {
      setSyncError(null)
      await triggerSync(syncVersion)
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : 'Sync failed')
    }
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never'
    return new Date(dateString).toLocaleString()
  }

  if (isLoading) {
    return (
      <AppShell>
        <PageContainer size="md">
          <LoadingState message="Loading admin settings..." />
        </PageContainer>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <PageContainer size="md">
        <PageHeader
          title="Admin Settings"
          description="Manage O*NET database and system configuration."
        />

        {/* O*NET Database Section */}
        <section className="surface p-6 mb-6">
          <div className="flex items-start gap-4 mb-6">
            <div className="w-12 h-12 rounded-xl bg-accent/15 flex items-center justify-center shrink-0">
              <IconDatabase size={24} className="text-accent" />
            </div>
            <div>
              <h2 className="text-lg font-display font-semibold text-default">
                O*NET Database
              </h2>
              <p className="text-sm text-muted mt-0.5">
                Sync occupation data from the official O*NET database for role mapping.
              </p>
            </div>
          </div>

          {/* Status Card */}
          <div className="bg-bg-muted rounded-lg p-4 mb-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-muted uppercase tracking-wide mb-1">Status</p>
                <Badge variant={status?.synced ? 'success' : 'warning'} dot>
                  {status?.synced ? 'Synced' : 'Not Synced'}
                </Badge>
              </div>
              <div>
                <p className="text-xs text-muted uppercase tracking-wide mb-1">Version</p>
                <p className="font-medium text-default">
                  {status?.version ? `v${status.version}` : '—'}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted uppercase tracking-wide mb-1">Occupations</p>
                <p className="font-medium text-default tabular-nums">
                  {status?.occupation_count?.toLocaleString() || '0'}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted uppercase tracking-wide mb-1">Last Synced</p>
                <p className="font-medium text-default text-sm">
                  {formatDate(status?.synced_at || null)}
                </p>
              </div>
            </div>
          </div>

          {/* Sync Controls */}
          <div className="flex flex-col sm:flex-row items-start sm:items-end gap-4">
            <div className="flex-1 w-full sm:w-auto">
              <label htmlFor="sync-version" className="block text-sm font-medium text-default mb-1.5">
                O*NET Version
              </label>
              <select
                id="sync-version"
                value={syncVersion}
                onChange={(e) => setSyncVersion(e.target.value)}
                className="input w-full sm:w-48"
                disabled={isSyncing}
              >
                <option value="30_1">v30.1 (Latest)</option>
                <option value="29_2">v29.2</option>
                <option value="29_1">v29.1</option>
                <option value="28_3">v28.3</option>
              </select>
            </div>

            <div className="flex gap-2">
              <Button
                variant="secondary"
                size="md"
                icon={<IconRefresh size={16} />}
                onClick={refresh}
                disabled={isSyncing}
              >
                Refresh
              </Button>
              <Button
                variant="primary"
                size="md"
                icon={isSyncing ? undefined : <IconDatabase size={16} />}
                onClick={handleSync}
                disabled={isSyncing}
              >
                {isSyncing ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Syncing...
                  </>
                ) : (
                  'Sync Database'
                )}
              </Button>
            </div>
          </div>

          {/* Sync Result */}
          {syncResult && (
            <div className="mt-4 p-4 bg-success/10 border border-success/20 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <IconCheck size={18} className="text-success" />
                <span className="font-medium text-success">Sync Completed Successfully</span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-muted">Version:</span>{' '}
                  <span className="text-default">v{syncResult.version}</span>
                </div>
                <div>
                  <span className="text-muted">Occupations:</span>{' '}
                  <span className="text-default">{syncResult.occupation_count.toLocaleString()}</span>
                </div>
                <div>
                  <span className="text-muted">Alternate Titles:</span>{' '}
                  <span className="text-default">{syncResult.alternate_title_count.toLocaleString()}</span>
                </div>
                <div>
                  <span className="text-muted">Tasks:</span>{' '}
                  <span className="text-default">{syncResult.task_count.toLocaleString()}</span>
                </div>
              </div>
            </div>
          )}

          {/* Error Display */}
          {(error || syncError) && (
            <div className="mt-4 p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
              <p className="text-sm text-destructive">{syncError || error}</p>
            </div>
          )}
        </section>

        {/* Info Section */}
        <section className="surface p-6">
          <h3 className="font-display font-semibold text-default mb-3">About O*NET Data</h3>
          <div className="text-sm text-muted space-y-2">
            <p>
              The O*NET database contains standardized occupation information including job titles,
              descriptions, and detailed work activities (DWAs) used for AI exposure analysis.
            </p>
            <p>
              Data is downloaded from the official{' '}
              <a
                href="https://www.onetcenter.org/database.html"
                target="_blank"
                rel="noopener noreferrer"
                className="text-accent hover:underline"
              >
                O*NET Resource Center
              </a>
              . Sync typically takes 1-2 minutes depending on your connection.
            </p>
          </div>
        </section>
      </PageContainer>
    </AppShell>
  )
}
