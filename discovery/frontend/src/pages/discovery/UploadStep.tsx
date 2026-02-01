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
      <h1 className="text-2xl font-bold mb-4">Upload Your Organization Data</h1>
      <p className="text-gray-600 mb-8">
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
          transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
          ${isDragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
          ${error ? 'border-red-500 bg-red-50' : ''}
        `}
      >
        {isUploading ? (
          <div className="flex flex-col items-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mb-4" />
            <p className="text-gray-600">Processing file...</p>
          </div>
        ) : uploadedFile ? (
          <div className="flex flex-col items-center">
            <svg
              className="h-12 w-12 text-green-500 mb-4"
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
            <p className="font-medium text-gray-900">{uploadedFile.name}</p>
            <p className="text-sm text-gray-500 mt-1">
              {(uploadedFile.size / 1024).toFixed(1)} KB
            </p>
            <button
              type="button"
              onClick={clearFile}
              className="mt-4 text-sm text-red-600 hover:text-red-700"
            >
              Remove file
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <svg
              className="h-12 w-12 text-gray-400 mb-4"
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
            <p className="text-gray-600 mb-2">Drag and drop your file here, or</p>
            <button
              type="button"
              onClick={handleBrowseClick}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
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
        <p className="mt-4 text-red-600" role="alert">
          {error.message}
        </p>
      )}

      {/* Column Preview */}
      {uploadedFile && uploadedFile.columns.length > 0 && (
        <div className="w-full max-w-lg mt-8">
          <h2 className="text-lg font-semibold mb-4">Detected Columns</h2>
          <div className="bg-gray-50 rounded-lg p-4">
            <ul className="grid grid-cols-2 gap-2">
              {uploadedFile.columns.map((column, index) => (
                <li
                  key={`${column}-${index}`}
                  className="flex items-center px-3 py-2 bg-white rounded border border-gray-200"
                >
                  <span className="text-sm font-mono">{column}</span>
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
                ? 'bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }
          `}
        >
          Continue
        </button>
      </div>
    </div>
  )
}
