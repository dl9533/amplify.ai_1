import { useState, useCallback, useEffect, useRef } from 'react'
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
  IconZap,
} from '../../components/ui/Icons'
import { useFileUpload } from '../../hooks/useFileUpload'
import { useIndustry } from '../../hooks/useIndustry'
import { IndustrySelector } from '../../components/features/discovery/IndustrySelector'
import { ColumnMappingUpdate } from '../../services/discoveryApi'

interface DetectedMapping {
  field: string
  column: string | null
  confidence: number
  alternatives: string[]
  required: boolean
}

// Tooltip definitions for each column mapping field
const FIELD_TOOLTIPS: Record<string, string> = {
  role: 'The job title or position name. This is the primary field used for O*NET occupation matching.',
  lob: 'Line of Business - the business unit or division (e.g., "Retail Banking", "Insurance", "Wealth Management").',
  department: 'The organizational department (e.g., "Engineering", "Sales", "HR").',
  geography: 'The location or region (e.g., "New York", "EMEA", "Remote").',
  headcount: 'The number of employees in this role. Used to calculate impact and prioritization.',
}

export function UploadStep() {
  const { sessionId } = useParams()
  const {
    file,
    uploading,
    uploadProgress,
    uploadError,
    uploadResult,
    uploadId,
    savingMappings,
    isLoadingExisting,
    handleDrop,
    handleFileSelect,
    clearFile,
    saveMappings,
  } = useFileUpload(sessionId || '')

  // Industry selection
  const {
    supersectors,
    selectedSector,
    isLoading: isLoadingIndustry,
    isSaving: isSavingIndustry,
    error: industryError,
    updateIndustry,
  } = useIndustry(sessionId)

  const [dragActive, setDragActive] = useState(false)
  const [columnMappings, setColumnMappings] = useState<Record<string, string>>({})
  const [hasInitializedMappings, setHasInitializedMappings] = useState(false)

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
  const detectedMappings: DetectedMapping[] = (uploadResult as { detected_mappings?: DetectedMapping[] })?.detected_mappings || []

  // Column mapping options - now includes LOB
  const mappingOptions = ['role', 'lob', 'department', 'geography', 'headcount']

  // Track whether mappings have been modified by user (to avoid re-saving on initial detection)
  const hasSavedMappings = useRef(false)
  const saveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Pre-populate column mappings from detected mappings (new upload)
  useEffect(() => {
    if (detectedMappings.length > 0 && !hasInitializedMappings) {
      const initialMappings: Record<string, string> = {}
      detectedMappings.forEach((dm) => {
        if (dm.column && dm.confidence >= 0.7) {
          initialMappings[dm.column] = dm.field
        }
      })
      if (Object.keys(initialMappings).length > 0) {
        setColumnMappings(initialMappings)
        setHasInitializedMappings(true)
      }
    }
  }, [detectedMappings, hasInitializedMappings])

  // Pre-populate column mappings from existing upload (navigating back)
  useEffect(() => {
    if (uploadResult?.column_mappings && !hasInitializedMappings) {
      // Backend stores as { fieldType: columnName }, convert to { columnName: fieldType }
      const existingMappings: Record<string, string> = {}
      Object.entries(uploadResult.column_mappings).forEach(([field, column]) => {
        if (column) {
          existingMappings[column] = field
        }
      })
      if (Object.keys(existingMappings).length > 0) {
        setColumnMappings(existingMappings)
        setHasInitializedMappings(true)
      }
    }
  }, [uploadResult?.column_mappings, hasInitializedMappings])

  // Auto-save column mappings to backend when they change
  // Uses debouncing to avoid excessive API calls
  useEffect(() => {
    // Skip if no upload ID or no role mapping yet
    if (!uploadId || !Object.values(columnMappings).includes('role')) {
      return
    }

    // Clear any pending save
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current)
    }

    // Debounce the save by 500ms
    saveTimeoutRef.current = setTimeout(async () => {
      // Convert from { columnName: fieldType } to { fieldType: columnName }
      const backendMappings: ColumnMappingUpdate = {}
      Object.entries(columnMappings).forEach(([column, field]) => {
        if (field && column) {
          (backendMappings as Record<string, string>)[field] = column
        }
      })

      const success = await saveMappings(backendMappings)
      if (success) {
        hasSavedMappings.current = true
      }
    }, 500)

    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current)
      }
    }
  }, [columnMappings, uploadId, saveMappings])

  // Get detected mapping for a column
  const getDetectedMapping = (column: string): DetectedMapping | undefined => {
    return detectedMappings.find((dm) => dm.column === column)
  }

  const handleColumnMapping = (column: string, mapping: string) => {
    setColumnMappings((prev) => {
      // Remove existing mapping for this value
      const cleaned = Object.fromEntries(
        Object.entries(prev).filter(([_, v]) => v !== mapping)
      )
      return { ...cleaned, [column]: mapping }
    })
  }

  // Can proceed if we have:
  // 1. Industry selected (required)
  // 2. Upload completed
  // 3. Role column mapped
  // 4. Not currently saving
  const hasRoleMapping = Object.values(columnMappings).includes('role')
  const hasIndustry = !!selectedSector
  const canProceed = hasIndustry && !!uploadResult && hasRoleMapping && !savingMappings && !isSavingIndustry

  // Show loading state while fetching existing uploads or industry data
  if (isLoadingExisting || isLoadingIndustry) {
    return (
      <AppShell>
        <DiscoveryWizard currentStep={1} canProceed={false}>
          <StepContent
            title="Upload Workforce Data"
            description="Import your organization's workforce data to identify automation opportunities."
          >
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="w-10 h-10 rounded-full border-2 border-accent border-t-transparent animate-spin mx-auto mb-3" />
                <p className="text-sm text-muted">Loading...</p>
              </div>
            </div>
          </StepContent>
        </DiscoveryWizard>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <DiscoveryWizard currentStep={1} canProceed={canProceed}>
        <StepContent
          title="Upload Workforce Data"
          description="Import your organization's workforce data to identify automation opportunities."
        >
          {/* Industry Selection - Required before upload */}
          <div className="surface p-5 mb-6">
            <IndustrySelector
              supersectors={supersectors}
              value={selectedSector}
              onChange={updateIndustry}
              disabled={false}
              isSaving={isSavingIndustry}
              error={industryError}
            />
          </div>

          {/* File dropzone - only enabled when industry is selected */}
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
                        {file?.name || uploadResult.file_name || 'Uploaded file'}
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
                <div className="flex items-center justify-between mb-1">
                  <h4 className="font-display font-medium text-default">
                    Map Your Columns
                  </h4>
                  <div className="flex items-center gap-2">
                    {savingMappings && (
                      <span className="inline-flex items-center gap-1 text-xs text-muted">
                        <span className="w-3 h-3 border-2 border-current/30 border-t-current rounded-full animate-spin" />
                        Saving...
                      </span>
                    )}
                    {detectedMappings.length > 0 && (
                      <span className="inline-flex items-center gap-1 text-xs text-accent">
                        <IconZap size={12} />
                        Auto-detected
                      </span>
                    )}
                  </div>
                </div>
                <p className="text-sm text-muted mb-4">
                  Tell us which columns contain the key information. Role column is required.
                  {detectedMappings.length > 0 && ' We\'ve pre-filled some mappings based on your column names.'}
                </p>

                {/* Field definitions legend */}
                <div className="mb-4 p-3 bg-bg-muted/50 rounded-lg">
                  <p className="text-xs font-medium text-muted mb-2">Column definitions:</p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-subtle">
                    {mappingOptions.map((opt) => (
                      <div key={opt} className="flex items-start gap-1.5">
                        <span className="font-medium text-default">
                          {opt === 'lob' ? 'LOB' : opt.charAt(0).toUpperCase() + opt.slice(1)}:
                        </span>
                        <span className="text-muted">{FIELD_TOOLTIPS[opt]?.split('.')[0]}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="space-y-3">
                  {detectedColumns.map((column) => {
                    const detected = getDetectedMapping(column)
                    const isAutoDetected = detected && detected.confidence >= 0.7

                    return (
                      <div
                        key={column}
                        className={`flex items-center gap-4 p-3 rounded-lg ${
                          isAutoDetected ? 'bg-accent/5 border border-accent/20' : 'bg-bg-muted'
                        }`}
                      >
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-default truncate">
                              {column}
                            </span>
                            {isAutoDetected && (
                              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 text-xs rounded bg-accent/10 text-accent">
                                <IconZap size={10} />
                                {Math.round(detected.confidence * 100)}%
                              </span>
                            )}
                          </div>
                        </div>
                        <select
                          value={columnMappings[column] || ''}
                          onChange={(e) => handleColumnMapping(column, e.target.value)}
                          className={`
                            px-3 py-1.5 text-sm
                            bg-bg-surface text-default
                            border rounded-md
                            focus:border-accent focus:ring-1 focus:ring-accent/30
                            ${isAutoDetected ? 'border-accent/30' : 'border-border'}
                          `}
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
                              {opt === 'lob' ? 'Line of Business' : opt.charAt(0).toUpperCase() + opt.slice(1)}
                              {opt === 'role' ? ' (required)' : ''}
                            </option>
                          ))}
                        </select>
                      </div>
                    )
                  })}
                </div>

                {/* Mapping status */}
                {!Object.values(columnMappings).includes('role') && (
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
