import { useState, useCallback } from 'react'

// Maximum file size: 10MB
export const MAX_FILE_SIZE = 10 * 1024 * 1024

// Maximum column name length
const MAX_COLUMN_NAME_LENGTH = 100

export interface UploadedFile {
  file: File
  name: string
  size: number
  type: string
  columns: string[]
}

export interface UseFileUploadOptions {
  acceptedTypes?: string[]
  onUploadComplete?: (file: UploadedFile) => void
  onError?: (error: Error) => void
}

export interface UseFileUploadReturn {
  uploadedFile: UploadedFile | null
  isUploading: boolean
  error: Error | null
  handleFileDrop: (files: FileList | File[]) => void
  handleFileSelect: (event: React.ChangeEvent<HTMLInputElement>) => void
  clearFile: () => void
}

/**
 * Sanitize column names by escaping HTML special characters and limiting length
 */
function sanitizeColumnName(name: string): string {
  // Escape HTML special characters to prevent XSS
  const escaped = name
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')

  // Limit column name length
  if (escaped.length > MAX_COLUMN_NAME_LENGTH) {
    return escaped.slice(0, MAX_COLUMN_NAME_LENGTH) + '...'
  }

  return escaped
}

async function parseCSVColumns(file: File): Promise<string[]> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (event) => {
      try {
        const text = event.target?.result as string
        const firstLine = text.split('\n')[0]
        const columns = firstLine
          .split(',')
          .map((col) => col.trim())
          .map(sanitizeColumnName)
        resolve(columns)
      } catch (err) {
        reject(new Error('Failed to parse CSV file'))
      }
    }
    reader.onerror = () => reject(new Error('Failed to read file'))
    reader.readAsText(file)
  })
}

export function useFileUpload({
  acceptedTypes = ['text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
  onUploadComplete,
  onError,
}: UseFileUploadOptions = {}): UseFileUploadReturn {
  const [uploadedFile, setUploadedFile] = useState<UploadedFile | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const processFile = useCallback(
    async (file: File) => {
      setIsUploading(true)
      setError(null)

      try {
        // Validate file size
        if (file.size > MAX_FILE_SIZE) {
          throw new Error(
            `File size exceeds maximum allowed size of ${MAX_FILE_SIZE / (1024 * 1024)}MB. Please upload a smaller file.`
          )
        }

        // Validate file type
        const isAccepted =
          acceptedTypes.includes(file.type) ||
          file.name.endsWith('.csv') ||
          file.name.endsWith('.xlsx')

        if (!isAccepted) {
          throw new Error('Invalid file type. Please upload a CSV or XLSX file.')
        }

        // Parse columns from the file
        let columns: string[] = []
        if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
          columns = await parseCSVColumns(file)
        } else {
          // For XLSX files, we'd need a library like xlsx
          // For now, return placeholder columns
          columns = ['Column A', 'Column B', 'Column C']
        }

        const uploadedFileData: UploadedFile = {
          file,
          name: file.name,
          size: file.size,
          type: file.type,
          columns,
        }

        setUploadedFile(uploadedFileData)
        onUploadComplete?.(uploadedFileData)
      } catch (err) {
        const errorObj = err instanceof Error ? err : new Error('Failed to process file')
        setError(errorObj)
        onError?.(errorObj)
      } finally {
        setIsUploading(false)
      }
    },
    [acceptedTypes, onUploadComplete, onError]
  )

  const handleFileDrop = useCallback(
    (files: FileList | File[]) => {
      const fileArray = Array.isArray(files) ? files : Array.from(files)
      if (fileArray.length > 0) {
        processFile(fileArray[0])
      }
    },
    [processFile]
  )

  const handleFileSelect = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const files = event.target.files
      if (files && files.length > 0) {
        processFile(files[0])
      }
    },
    [processFile]
  )

  const clearFile = useCallback(() => {
    setUploadedFile(null)
    setError(null)
  }, [])

  return {
    uploadedFile,
    isUploading,
    error,
    handleFileDrop,
    handleFileSelect,
    clearFile,
  }
}
