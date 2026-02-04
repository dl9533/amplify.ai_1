import { useState, useCallback } from 'react'
import { uploadApi, UploadResponse, ColumnMappingUpdate } from '../services/discoveryApi'

// Maximum file size: 10MB
export const MAX_FILE_SIZE = 10 * 1024 * 1024

// Accepted file types
const ACCEPTED_TYPES = ['text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']

export interface UseFileUploadReturn {
  file: File | null
  uploading: boolean
  uploadProgress: number
  uploadError: string | null
  uploadResult: UploadResponse | null
  uploadId: string | null
  savingMappings: boolean
  handleDrop: (file: File) => void
  handleFileSelect: (file: File) => void
  clearFile: () => void
  saveMappings: (mappings: ColumnMappingUpdate) => Promise<boolean>
}

/**
 * Hook for handling file uploads in the Discovery workflow.
 * Uploads files to the backend and returns schema detection results.
 */
export function useFileUpload(sessionId: string): UseFileUploadReturn {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null)
  const [uploadId, setUploadId] = useState<string | null>(null)
  const [savingMappings, setSavingMappings] = useState(false)

  const validateFile = useCallback((file: File): string | null => {
    // Validate file size
    if (file.size > MAX_FILE_SIZE) {
      return `File size exceeds maximum allowed size of ${MAX_FILE_SIZE / (1024 * 1024)}MB`
    }

    // Validate file type
    const isAccepted =
      ACCEPTED_TYPES.includes(file.type) ||
      file.name.endsWith('.csv') ||
      file.name.endsWith('.xlsx') ||
      file.name.endsWith('.xls')

    if (!isAccepted) {
      return 'Invalid file type. Please upload a CSV or Excel file.'
    }

    return null
  }, [])

  const processFile = useCallback(
    async (uploadFile: File) => {
      // Validate file first
      const validationError = validateFile(uploadFile)
      if (validationError) {
        setUploadError(validationError)
        return
      }

      setFile(uploadFile)
      setUploading(true)
      setUploadProgress(0)
      setUploadError(null)
      setUploadResult(null)

      try {
        const result = await uploadApi.upload(sessionId, uploadFile, (progress) => {
          setUploadProgress(progress)
        })

        setUploadResult(result)
        // Capture the upload ID from the response
        // Backend returns 'id' field
        if (result.id) {
          setUploadId(result.id)
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to upload file'
        setUploadError(errorMessage)
        setFile(null)
        setUploadId(null)
      } finally {
        setUploading(false)
      }
    },
    [sessionId, validateFile]
  )

  const handleDrop = useCallback(
    (droppedFile: File) => {
      processFile(droppedFile)
    },
    [processFile]
  )

  const handleFileSelect = useCallback(
    (selectedFile: File) => {
      processFile(selectedFile)
    },
    [processFile]
  )

  const clearFile = useCallback(() => {
    setFile(null)
    setUploadProgress(0)
    setUploadError(null)
    setUploadResult(null)
    setUploadId(null)
  }, [])

  /**
   * Save column mappings for the current upload.
   * This must be called before navigating to the Map Roles step.
   * @param mappings - Maps field types (role, lob, etc.) to column names
   * @returns true if successful, false otherwise
   */
  const saveMappings = useCallback(async (mappings: ColumnMappingUpdate): Promise<boolean> => {
    if (!uploadId) {
      setUploadError('No upload to save mappings for')
      return false
    }

    try {
      setSavingMappings(true)
      setUploadError(null)
      await uploadApi.saveMappings(uploadId, mappings)
      return true
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save column mappings'
      setUploadError(errorMessage)
      return false
    } finally {
      setSavingMappings(false)
    }
  }, [uploadId])

  return {
    file,
    uploading,
    uploadProgress,
    uploadError,
    uploadResult,
    uploadId,
    savingMappings,
    handleDrop,
    handleFileSelect,
    clearFile,
    saveMappings,
  }
}
