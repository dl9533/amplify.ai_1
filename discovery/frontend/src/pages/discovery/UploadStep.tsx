import { useState, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { AppShell } from '../../components/layout/AppShell'
import { DiscoveryWizard, StepContent } from '../../components/layout/DiscoveryWizard'
import { Button } from '../../components/ui/Button'
import {
  IconUpload,
  IconFileSpreadsheet,
  IconCheck,
  IconX,
  IconAlertCircle,
} from '../../components/ui/Icons'
import { useFileUpload } from '../../hooks/useFileUpload'

export function UploadStep() {
  const { sessionId } = useParams()
  const {
    file,
    uploading,
    uploadProgress,
    uploadError,
    uploadResult,
    handleDrop,
    handleFileSelect,
    clearFile,
  } = useFileUpload(sessionId || '')

  const [dragActive, setDragActive] = useState(false)
  const [columnMappings, setColumnMappings] = useState<Record<string, string>>({})

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
  }, [])

  const handleDropFiles = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setDragActive(false)
      const files = Array.from(e.dataTransfer.files)
      if (files.length > 0) {
        handleDrop(files[0])
      }
    },
    [handleDrop]
  )

  const handleFileInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files
      if (files && files.length > 0) {
        handleFileSelect(files[0])
      }
    },
    [handleFileSelect]
  )

  // Detected columns from upload
  const detectedColumns = uploadResult?.detected_schema || []

  // Column mapping options
  const mappingOptions = ['role', 'department', 'geography', 'headcount']

  const handleColumnMapping = (column: string, mapping: string) => {
    setColumnMappings((prev) => {
      // Remove existing mapping for this value
      const cleaned = Object.fromEntries(
        Object.entries(prev).filter(([_, v]) => v !== mapping)
      )
      return { ...cleaned, [column]: mapping }
    })
  }

  const canProceed = !!uploadResult && !!columnMappings['role']

  return (
    <AppShell>
      <DiscoveryWizard currentStep={1} canProceed={canProceed}>
        <StepContent
          title="Upload Workforce Data"
          description="Import your organization's workforce data to identify automation opportunities."
        >
          {/* File dropzone */}
          {!uploadResult ? (
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDropFiles}
              className={`
                relative border-2 border-dashed rounded-xl p-12
                flex flex-col items-center justify-center
                transition-all duration-200
                ${dragActive ? 'border-accent bg-accent/5' : 'border-border hover:border-accent/50'}
                ${uploading ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
              `}
            >
              <input
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={handleFileInputChange}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                disabled={uploading}
              />

              {/* Upload icon */}
              <div
                className={`
                  w-16 h-16 rounded-2xl flex items-center justify-center mb-4
                  ${dragActive ? 'bg-accent/15 text-accent' : 'bg-bg-muted text-subtle'}
                  transition-all duration-200
                `}
              >
                <IconUpload size={28} />
              </div>

              {/* Upload text */}
              <h3 className="font-display font-semibold text-default mb-1">
                {dragActive ? 'Drop file here' : 'Drag and drop your file'}
              </h3>
              <p className="text-sm text-muted mb-4">
                or <span className="text-accent underline">browse</span> to select
              </p>

              {/* File types */}
              <div className="flex items-center gap-4 text-xs text-subtle">
                <span className="flex items-center gap-1">
                  <IconFileSpreadsheet size={14} />
                  CSV
                </span>
                <span className="flex items-center gap-1">
                  <IconFileSpreadsheet size={14} />
                  Excel (.xlsx)
                </span>
                <span>Max 10MB</span>
              </div>

              {/* Upload progress */}
              {uploading && (
                <div className="absolute inset-0 flex items-center justify-center bg-base/80 rounded-xl">
                  <div className="text-center">
                    <div className="w-12 h-12 rounded-full border-2 border-accent border-t-transparent animate-spin mx-auto mb-3" />
                    <p className="text-sm text-default">Uploading...</p>
                    {uploadProgress > 0 && (
                      <p className="text-xs text-muted mt-1">{uploadProgress}%</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          ) : (
            /* Upload success - show file info and column mapping */
            <div className="space-y-6">
              {/* File info card */}
              <div className="surface p-5">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-success/10 flex items-center justify-center">
                      <IconCheck size={24} className="text-success" />
                    </div>
                    <div>
                      <h4 className="font-display font-medium text-default">
                        {file?.name || 'Uploaded file'}
                      </h4>
                      <p className="text-sm text-muted">
                        {uploadResult.row_count?.toLocaleString() || 0} rows detected
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={<IconX size={16} />}
                    onClick={clearFile}
                  >
                    Remove
                  </Button>
                </div>
              </div>

              {/* Column mapping */}
              <div className="surface p-5">
                <h4 className="font-display font-medium text-default mb-1">
                  Map Your Columns
                </h4>
                <p className="text-sm text-muted mb-4">
                  Tell us which columns contain the key information. Role column is required.
                </p>

                <div className="space-y-3">
                  {detectedColumns.map((column) => (
                    <div
                      key={column}
                      className="flex items-center gap-4 p-3 bg-bg-muted rounded-lg"
                    >
                      <div className="flex-1 min-w-0">
                        <span className="text-sm font-medium text-default truncate block">
                          {column}
                        </span>
                      </div>
                      <select
                        value={columnMappings[column] || ''}
                        onChange={(e) => handleColumnMapping(column, e.target.value)}
                        className="
                          px-3 py-1.5 text-sm
                          bg-bg-surface text-default
                          border border-border rounded-md
                          focus:border-accent focus:ring-1 focus:ring-accent/30
                        "
                      >
                        <option value="">Skip column</option>
                        {mappingOptions.map((opt) => (
                          <option
                            key={opt}
                            value={opt}
                            disabled={
                              Object.values(columnMappings).includes(opt) &&
                              columnMappings[column] !== opt
                            }
                          >
                            {opt.charAt(0).toUpperCase() + opt.slice(1)}
                            {opt === 'role' ? ' (required)' : ''}
                          </option>
                        ))}
                      </select>
                    </div>
                  ))}
                </div>

                {/* Mapping status */}
                {!columnMappings['role'] && (
                  <div className="mt-4 p-3 bg-warning/10 border border-warning/20 rounded-lg flex items-start gap-3">
                    <IconAlertCircle size={18} className="text-warning shrink-0 mt-0.5" />
                    <p className="text-sm text-warning">
                      Please map at least the Role column to continue.
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Error state */}
          {uploadError && (
            <div className="mt-4 p-4 bg-destructive/10 border border-destructive/20 rounded-lg flex items-start gap-3">
              <IconAlertCircle size={18} className="text-destructive shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-destructive">Upload failed</p>
                <p className="text-sm text-destructive/80 mt-0.5">{uploadError}</p>
              </div>
            </div>
          )}
        </StepContent>
      </DiscoveryWizard>
    </AppShell>
  )
}
