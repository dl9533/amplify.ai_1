import { useCallback, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useFileUpload, type UploadedFile } from '@/hooks/useFileUpload'

export function UploadStep() {
  // sessionId will be used for API integration when uploading files to the backend
  const { sessionId: _sessionId } = useParams<{ sessionId: string }>()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isDragOver, setIsDragOver] = useState(false)

  const { uploadedFile, isUploading, error, handleFileDrop, handleFileSelect, clearFile } =
    useFileUpload()

  const handleDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    event.stopPropagation()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    event.stopPropagation()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault()
      event.stopPropagation()
      setIsDragOver(false)

      const files = event.dataTransfer.files
      if (files && files.length > 0) {
        handleFileDrop(files)
      }
    },
    [handleFileDrop]
  )

  const handleBrowseClick = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleDropZoneKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLDivElement>) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault()
        fileInputRef.current?.click()
      }
    },
    []
  )

  const isUploadComplete = uploadedFile !== null && !isUploading

  return (
    <div className="flex flex-col items-center justify-center p-8">
      <h1 className="text-2xl font-bold mb-4 text-foreground">Upload Your Organization Data</h1>
      <p className="text-foreground-muted mb-8">
        Upload a CSV or XLSX file containing your organization&apos;s data for analysis.
      </p>

      {/* File Drop Zone */}
      <div
        data-testid="file-dropzone"
        role="button"
        tabIndex={0}
        aria-label="File upload drop zone. Press Enter or Space to open file selector."
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onKeyDown={handleDropZoneKeyDown}
        className={`
          w-full max-w-lg p-12 border-2 border-dashed rounded-lg text-center cursor-pointer
          transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background
          ${isDragOver ? 'border-primary bg-primary/10' : 'border-border hover:border-border'}
          ${error ? 'border-destructive bg-destructive/10' : ''}
        `}
      >
        {isUploading ? (
          <div className="flex flex-col items-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-4" />
            <p className="text-foreground-muted">Processing file...</p>
          </div>
        ) : uploadedFile ? (
          <div className="flex flex-col items-center">
            <svg
              className="h-12 w-12 text-success mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="font-medium text-foreground">{uploadedFile.name}</p>
            <p className="text-sm text-foreground-muted mt-1">
              {(uploadedFile.size / 1024).toFixed(1)} KB
            </p>
            <button
              type="button"
              onClick={clearFile}
              className="mt-4 text-sm text-destructive hover:text-destructive/80"
            >
              Remove file
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <svg
              className="h-12 w-12 text-foreground-subtle mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
            <p className="text-foreground-muted mb-2">Drag and drop your file here, or</p>
            <button
              type="button"
              onClick={handleBrowseClick}
              className="btn-primary btn-md rounded-md"
            >
              Browse files
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx"
              onChange={handleFileSelect}
              className="hidden"
              aria-label="Upload file"
            />
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <p className="mt-4 text-destructive" role="alert">
          {error.message}
        </p>
      )}

      {/* Column Preview */}
      {uploadedFile && uploadedFile.columns.length > 0 && (
        <div className="w-full max-w-lg mt-8">
          <h2 className="text-lg font-semibold mb-4 text-foreground">Detected Columns</h2>
          <div className="bg-background-muted rounded-lg p-4">
            <ul className="grid grid-cols-2 gap-2">
              {uploadedFile.columns.map((column, index) => (
                <li
                  key={`${column}-${index}`}
                  className="flex items-center px-3 py-2 bg-background rounded border border-border"
                >
                  <span className="text-sm font-mono text-foreground">{column}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Continue Button */}
      <div className="w-full max-w-lg mt-8 flex justify-end">
        <button
          type="button"
          disabled={!isUploadComplete}
          className={`
            px-6 py-3 rounded-md font-medium
            ${
              isUploadComplete
                ? 'btn-primary'
                : 'bg-background-muted text-foreground-subtle cursor-not-allowed'
            }
          `}
        >
          Continue
        </button>
      </div>
    </div>
  )
}
