import { useState, useRef, useCallback } from 'react'

export interface FileDropZoneProps {
  onFileDrop: (file: File) => void
  onError?: (error: string) => void
  accept?: string[]
  maxSizeMB?: number
  isUploading?: boolean
  progress?: number
}

export function FileDropZone({
  onFileDrop,
  onError,
  accept,
  maxSizeMB,
  isUploading = false,
  progress = 0,
}: FileDropZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const validateFile = useCallback(
    (file: File): boolean => {
      // Check file extension if accept is provided
      if (accept && accept.length > 0) {
        const fileName = file.name.toLowerCase()
        const hasValidExtension = accept.some((ext) =>
          fileName.endsWith(ext.toLowerCase())
        )
        if (!hasValidExtension) {
          onError?.(`Unsupported file type. Accepted types: ${accept.join(', ')}`)
          return false
        }
      }

      // Check file size if maxSizeMB is provided
      if (maxSizeMB) {
        const maxSizeBytes = maxSizeMB * 1024 * 1024
        if (file.size > maxSizeBytes) {
          onError?.(`File size exceeds ${maxSizeMB} MB limit`)
          return false
        }
      }

      return true
    },
    [accept, maxSizeMB, onError]
  )

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault()
      e.stopPropagation()
      setIsDragOver(false)

      const file = e.dataTransfer.files[0]
      if (file && validateFile(file)) {
        onFileDrop(file)
      }
    },
    [onFileDrop, validateFile]
  )

  const handleDragEnter = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const handleFileInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (file && validateFile(file)) {
        onFileDrop(file)
      }
    },
    [onFileDrop, validateFile]
  )

  const handleBrowseClick = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault()
        fileInputRef.current?.click()
      }
    },
    []
  )

  const acceptString = accept?.join(',')

  return (
    <div
      data-testid="file-dropzone"
      role="region"
      aria-label="File upload drop zone"
      tabIndex={0}
      onDrop={handleDrop}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onKeyDown={handleKeyDown}
      className={`
        flex flex-col items-center justify-center
        p-8 border-2 border-dashed rounded-lg
        transition-colors duration-150 cursor-pointer
        focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background
        ${isDragOver ? 'border-primary bg-primary/5' : 'border-border hover:border-foreground-subtle'}
        ${isUploading ? 'pointer-events-none opacity-75' : ''}
      `}
    >
      {isUploading ? (
        <div className="w-full max-w-xs">
          <div
            role="progressbar"
            aria-valuenow={progress}
            aria-valuemin={0}
            aria-valuemax={100}
            className="w-full bg-background-accent rounded-full h-2.5"
          >
            <div
              className="bg-primary h-2.5 rounded-full transition-all duration-150"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-center text-sm text-foreground-muted mt-2 tabular-nums">{progress}%</p>
        </div>
      ) : (
        <>
          <svg
            className="w-12 h-12 text-foreground-subtle mb-4"
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
          <p className="text-foreground-muted mb-2">
            Drag and drop your file here, or
          </p>
          <button
            type="button"
            onClick={handleBrowseClick}
            className="text-primary hover:text-primary/80 font-medium underline transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background rounded"
          >
            Browse
          </button>
          {maxSizeMB && (
            <p className="text-sm text-foreground-subtle mt-2">
              Maximum {maxSizeMB} MB
            </p>
          )}
          {accept && (
            <p className="text-sm text-foreground-subtle mt-1">
              Accepted formats: {accept.join(', ')}
            </p>
          )}
        </>
      )}
      <input
        ref={fileInputRef}
        type="file"
        accept={acceptString}
        onChange={handleFileInputChange}
        className="hidden"
        aria-hidden="true"
      />
    </div>
  )
}
