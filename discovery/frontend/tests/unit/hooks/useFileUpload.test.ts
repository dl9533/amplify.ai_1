import { renderHook, act, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeEach } from 'vitest'
import { useFileUpload, MAX_FILE_SIZE } from '@/hooks/useFileUpload'
import { mockUploadApi, resetAllMocks } from '../../__mocks__/services'

describe('useFileUpload', () => {
  const sessionId = 'test-session-123'

  beforeEach(() => {
    resetAllMocks()
  })

  const createMockFile = (
    name: string,
    size: number,
    type: string
  ): File => {
    const file = new File(['test content'], name, { type })
    Object.defineProperty(file, 'size', { value: size })
    return file
  }

  describe('initial state', () => {
    it('starts with null file', () => {
      const { result } = renderHook(() => useFileUpload(sessionId))

      expect(result.current.file).toBeNull()
    })

    it('starts with uploading as false', () => {
      const { result } = renderHook(() => useFileUpload(sessionId))

      expect(result.current.uploading).toBe(false)
    })

    it('starts with uploadProgress at 0', () => {
      const { result } = renderHook(() => useFileUpload(sessionId))

      expect(result.current.uploadProgress).toBe(0)
    })

    it('starts with uploadError as null', () => {
      const { result } = renderHook(() => useFileUpload(sessionId))

      expect(result.current.uploadError).toBeNull()
    })

    it('starts with uploadResult as null', () => {
      const { result } = renderHook(() => useFileUpload(sessionId))

      expect(result.current.uploadResult).toBeNull()
    })

    it('provides all required functions', () => {
      const { result } = renderHook(() => useFileUpload(sessionId))

      expect(typeof result.current.handleDrop).toBe('function')
      expect(typeof result.current.handleFileSelect).toBe('function')
      expect(typeof result.current.clearFile).toBe('function')
    })
  })

  describe('successful file upload', () => {
    it('uploads a valid CSV file and returns result', async () => {
      const { result } = renderHook(() => useFileUpload(sessionId))
      const mockFile = createMockFile('test.csv', 1024, 'text/csv')

      await act(async () => {
        result.current.handleDrop(mockFile)
      })

      await waitFor(() => {
        expect(result.current.uploadResult).not.toBeNull()
      })

      expect(result.current.file?.name).toBe('test.csv')
      expect(result.current.uploadResult?.filename).toBe('workforce.csv')
      expect(result.current.uploadResult?.row_count).toBe(150)
      expect(result.current.uploadResult?.detected_schema).toEqual([
        'Role', 'Department', 'Location', 'Headcount'
      ])
      expect(result.current.uploading).toBe(false)
      expect(result.current.uploadError).toBeNull()
    })

    it('calls uploadApi.upload with correct parameters', async () => {
      const { result } = renderHook(() => useFileUpload(sessionId))
      const mockFile = createMockFile('test.csv', 1024, 'text/csv')

      await act(async () => {
        result.current.handleDrop(mockFile)
      })

      await waitFor(() => {
        expect(mockUploadApi.upload).toHaveBeenCalled()
      })

      expect(mockUploadApi.upload).toHaveBeenCalledWith(
        sessionId,
        mockFile,
        expect.any(Function) // progress callback
      )
    })

    it('accepts XLSX files', async () => {
      const { result } = renderHook(() => useFileUpload(sessionId))
      const mockFile = createMockFile(
        'test.xlsx',
        1024,
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      )

      await act(async () => {
        result.current.handleDrop(mockFile)
      })

      await waitFor(() => {
        expect(result.current.uploadResult).not.toBeNull()
      })

      expect(result.current.file?.name).toBe('test.xlsx')
      expect(result.current.uploadError).toBeNull()
    })

    it('accepts XLS files by extension', async () => {
      const { result } = renderHook(() => useFileUpload(sessionId))
      const mockFile = createMockFile('test.xls', 1024, 'application/octet-stream')

      await act(async () => {
        result.current.handleFileSelect(mockFile)
      })

      await waitFor(() => {
        expect(result.current.uploadResult).not.toBeNull()
      })

      expect(result.current.uploadError).toBeNull()
    })
  })

  describe('file size validation', () => {
    it('rejects files larger than MAX_FILE_SIZE', async () => {
      const { result } = renderHook(() => useFileUpload(sessionId))
      const oversizedFile = createMockFile(
        'large.csv',
        MAX_FILE_SIZE + 1,
        'text/csv'
      )

      await act(async () => {
        result.current.handleDrop(oversizedFile)
      })

      expect(result.current.uploadError).toContain('File size exceeds')
      expect(result.current.uploadError).toContain('10MB')
      expect(result.current.uploadResult).toBeNull()
      expect(mockUploadApi.upload).not.toHaveBeenCalled()
    })

    it('accepts files at exactly MAX_FILE_SIZE', async () => {
      const { result } = renderHook(() => useFileUpload(sessionId))
      const maxSizeFile = createMockFile('exact.csv', MAX_FILE_SIZE, 'text/csv')

      await act(async () => {
        result.current.handleDrop(maxSizeFile)
      })

      await waitFor(() => {
        expect(result.current.uploadResult).not.toBeNull()
      })

      expect(result.current.uploadError).toBeNull()
    })
  })

  describe('file type validation', () => {
    it('rejects files with invalid type', async () => {
      const { result } = renderHook(() => useFileUpload(sessionId))
      const invalidFile = createMockFile('document.pdf', 1024, 'application/pdf')

      await act(async () => {
        result.current.handleDrop(invalidFile)
      })

      expect(result.current.uploadError).toContain('Invalid file type')
      expect(result.current.uploadResult).toBeNull()
      expect(mockUploadApi.upload).not.toHaveBeenCalled()
    })

    it('rejects text files that are not CSV', async () => {
      const { result } = renderHook(() => useFileUpload(sessionId))
      const textFile = createMockFile('document.txt', 1024, 'text/plain')

      await act(async () => {
        result.current.handleDrop(textFile)
      })

      expect(result.current.uploadError).toContain('Invalid file type')
    })

    it('accepts CSV files with .csv extension regardless of MIME type', async () => {
      const { result } = renderHook(() => useFileUpload(sessionId))
      const csvFile = createMockFile('data.csv', 1024, 'application/octet-stream')

      await act(async () => {
        result.current.handleDrop(csvFile)
      })

      await waitFor(() => {
        expect(result.current.uploadResult).not.toBeNull()
      })

      expect(result.current.uploadError).toBeNull()
    })
  })

  describe('upload errors', () => {
    it('handles API errors gracefully', async () => {
      mockUploadApi.upload.mockRejectedValueOnce(new Error('Network error'))

      const { result } = renderHook(() => useFileUpload(sessionId))
      const mockFile = createMockFile('test.csv', 1024, 'text/csv')

      await act(async () => {
        result.current.handleDrop(mockFile)
      })

      await waitFor(() => {
        expect(result.current.uploadError).not.toBeNull()
      })

      expect(result.current.uploadError).toBe('Network error')
      expect(result.current.uploadResult).toBeNull()
      expect(result.current.file).toBeNull()
    })

    it('handles non-Error API rejections', async () => {
      mockUploadApi.upload.mockRejectedValueOnce('Unknown error')

      const { result } = renderHook(() => useFileUpload(sessionId))
      const mockFile = createMockFile('test.csv', 1024, 'text/csv')

      await act(async () => {
        result.current.handleDrop(mockFile)
      })

      await waitFor(() => {
        expect(result.current.uploadError).not.toBeNull()
      })

      expect(result.current.uploadError).toBe('Failed to upload file')
    })
  })

  describe('clearFile function', () => {
    it('clears the uploaded file and result', async () => {
      const { result } = renderHook(() => useFileUpload(sessionId))
      const mockFile = createMockFile('test.csv', 1024, 'text/csv')

      await act(async () => {
        result.current.handleDrop(mockFile)
      })

      await waitFor(() => {
        expect(result.current.uploadResult).not.toBeNull()
      })

      act(() => {
        result.current.clearFile()
      })

      expect(result.current.file).toBeNull()
      expect(result.current.uploadResult).toBeNull()
      expect(result.current.uploadProgress).toBe(0)
    })

    it('clears any existing error', async () => {
      const { result } = renderHook(() => useFileUpload(sessionId))
      const invalidFile = createMockFile('document.pdf', 1024, 'application/pdf')

      await act(async () => {
        result.current.handleDrop(invalidFile)
      })

      expect(result.current.uploadError).not.toBeNull()

      act(() => {
        result.current.clearFile()
      })

      expect(result.current.uploadError).toBeNull()
    })

    it('can be called when no file is uploaded', () => {
      const { result } = renderHook(() => useFileUpload(sessionId))

      // Should not throw
      act(() => {
        result.current.clearFile()
      })

      expect(result.current.file).toBeNull()
      expect(result.current.uploadError).toBeNull()
    })
  })

  describe('handleFileSelect', () => {
    it('processes files via handleFileSelect', async () => {
      const { result } = renderHook(() => useFileUpload(sessionId))
      const mockFile = createMockFile('selected.csv', 1024, 'text/csv')

      await act(async () => {
        result.current.handleFileSelect(mockFile)
      })

      await waitFor(() => {
        expect(result.current.uploadResult).not.toBeNull()
      })

      expect(result.current.file?.name).toBe('selected.csv')
    })
  })
})
