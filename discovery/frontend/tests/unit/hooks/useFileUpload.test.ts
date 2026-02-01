import { renderHook, act, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useFileUpload, MAX_FILE_SIZE } from '@/hooks/useFileUpload'

// Mock FileReader
class MockFileReader {
  result: string | null = null
  onload: ((event: ProgressEvent<FileReader>) => void) | null = null
  onerror: ((event: ProgressEvent<FileReader>) => void) | null = null

  readAsText(file: File) {
    // Simulate async read
    setTimeout(() => {
      if (this.onload) {
        this.result = 'Column1, Column2, Column3\nvalue1, value2, value3'
        this.onload({ target: this } as ProgressEvent<FileReader>)
      }
    }, 0)
  }
}

// Store original FileReader
const OriginalFileReader = global.FileReader

describe('useFileUpload', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    // @ts-expect-error - Mocking FileReader
    global.FileReader = MockFileReader
  })

  afterEach(() => {
    global.FileReader = OriginalFileReader
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
    it('starts with null uploadedFile', () => {
      const { result } = renderHook(() => useFileUpload())

      expect(result.current.uploadedFile).toBeNull()
    })

    it('starts with isUploading as false', () => {
      const { result } = renderHook(() => useFileUpload())

      expect(result.current.isUploading).toBe(false)
    })

    it('starts with error as null', () => {
      const { result } = renderHook(() => useFileUpload())

      expect(result.current.error).toBeNull()
    })

    it('provides all required functions', () => {
      const { result } = renderHook(() => useFileUpload())

      expect(typeof result.current.handleFileDrop).toBe('function')
      expect(typeof result.current.handleFileSelect).toBe('function')
      expect(typeof result.current.clearFile).toBe('function')
    })
  })

  describe('successful file upload', () => {
    it('processes a valid CSV file', async () => {
      const { result } = renderHook(() => useFileUpload())
      const mockFile = createMockFile('test.csv', 1024, 'text/csv')

      await act(async () => {
        result.current.handleFileDrop([mockFile])
      })

      await waitFor(() => {
        expect(result.current.uploadedFile).not.toBeNull()
      })

      expect(result.current.uploadedFile?.name).toBe('test.csv')
      expect(result.current.uploadedFile?.size).toBe(1024)
      expect(result.current.uploadedFile?.type).toBe('text/csv')
      expect(result.current.isUploading).toBe(false)
      expect(result.current.error).toBeNull()
    })

    it('parses column names from CSV', async () => {
      const { result } = renderHook(() => useFileUpload())
      const mockFile = createMockFile('test.csv', 1024, 'text/csv')

      await act(async () => {
        result.current.handleFileDrop([mockFile])
      })

      await waitFor(() => {
        expect(result.current.uploadedFile).not.toBeNull()
      })

      expect(result.current.uploadedFile?.columns).toEqual([
        'Column1',
        'Column2',
        'Column3',
      ])
    })

    it('calls onUploadComplete callback on success', async () => {
      const onUploadComplete = vi.fn()
      const { result } = renderHook(() =>
        useFileUpload({ onUploadComplete })
      )
      const mockFile = createMockFile('test.csv', 1024, 'text/csv')

      await act(async () => {
        result.current.handleFileDrop([mockFile])
      })

      await waitFor(() => {
        expect(onUploadComplete).toHaveBeenCalled()
      })

      expect(onUploadComplete).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'test.csv',
          size: 1024,
        })
      )
    })

    it('accepts XLSX files by extension', async () => {
      const { result } = renderHook(() => useFileUpload())
      const mockFile = createMockFile(
        'test.xlsx',
        1024,
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      )

      await act(async () => {
        result.current.handleFileDrop([mockFile])
      })

      await waitFor(() => {
        expect(result.current.uploadedFile).not.toBeNull()
      })

      expect(result.current.uploadedFile?.name).toBe('test.xlsx')
      expect(result.current.error).toBeNull()
    })
  })

  describe('file size validation error', () => {
    it('rejects files larger than MAX_FILE_SIZE', async () => {
      const { result } = renderHook(() => useFileUpload())
      const oversizedFile = createMockFile(
        'large.csv',
        MAX_FILE_SIZE + 1,
        'text/csv'
      )

      await act(async () => {
        result.current.handleFileDrop([oversizedFile])
      })

      await waitFor(() => {
        expect(result.current.error).not.toBeNull()
      })

      expect(result.current.error?.message).toContain('File size exceeds')
      expect(result.current.error?.message).toContain('10MB')
      expect(result.current.uploadedFile).toBeNull()
    })

    it('calls onError callback for oversized files', async () => {
      const onError = vi.fn()
      const { result } = renderHook(() => useFileUpload({ onError }))
      const oversizedFile = createMockFile(
        'large.csv',
        MAX_FILE_SIZE + 1,
        'text/csv'
      )

      await act(async () => {
        result.current.handleFileDrop([oversizedFile])
      })

      await waitFor(() => {
        expect(onError).toHaveBeenCalled()
      })

      expect(onError).toHaveBeenCalledWith(expect.any(Error))
    })

    it('accepts files at exactly MAX_FILE_SIZE', async () => {
      const { result } = renderHook(() => useFileUpload())
      const maxSizeFile = createMockFile('exact.csv', MAX_FILE_SIZE, 'text/csv')

      await act(async () => {
        result.current.handleFileDrop([maxSizeFile])
      })

      await waitFor(() => {
        expect(result.current.uploadedFile).not.toBeNull()
      })

      expect(result.current.error).toBeNull()
    })
  })

  describe('invalid file type error', () => {
    it('rejects files with invalid type', async () => {
      const { result } = renderHook(() => useFileUpload())
      const invalidFile = createMockFile('document.pdf', 1024, 'application/pdf')

      await act(async () => {
        result.current.handleFileDrop([invalidFile])
      })

      await waitFor(() => {
        expect(result.current.error).not.toBeNull()
      })

      expect(result.current.error?.message).toContain('Invalid file type')
      expect(result.current.uploadedFile).toBeNull()
    })

    it('rejects text files that are not CSV', async () => {
      const { result } = renderHook(() => useFileUpload())
      const textFile = createMockFile('document.txt', 1024, 'text/plain')

      await act(async () => {
        result.current.handleFileDrop([textFile])
      })

      await waitFor(() => {
        expect(result.current.error).not.toBeNull()
      })

      expect(result.current.error?.message).toContain('Invalid file type')
    })

    it('calls onError callback for invalid file types', async () => {
      const onError = vi.fn()
      const { result } = renderHook(() => useFileUpload({ onError }))
      const invalidFile = createMockFile('image.png', 1024, 'image/png')

      await act(async () => {
        result.current.handleFileDrop([invalidFile])
      })

      await waitFor(() => {
        expect(onError).toHaveBeenCalled()
      })
    })

    it('accepts CSV files with .csv extension regardless of MIME type', async () => {
      const { result } = renderHook(() => useFileUpload())
      // Some systems report CSV with different MIME types
      const csvFile = createMockFile('data.csv', 1024, 'application/octet-stream')

      await act(async () => {
        result.current.handleFileDrop([csvFile])
      })

      await waitFor(() => {
        expect(result.current.uploadedFile).not.toBeNull()
      })

      expect(result.current.error).toBeNull()
    })
  })

  describe('clearFile function', () => {
    it('clears the uploaded file', async () => {
      const { result } = renderHook(() => useFileUpload())
      const mockFile = createMockFile('test.csv', 1024, 'text/csv')

      await act(async () => {
        result.current.handleFileDrop([mockFile])
      })

      await waitFor(() => {
        expect(result.current.uploadedFile).not.toBeNull()
      })

      act(() => {
        result.current.clearFile()
      })

      expect(result.current.uploadedFile).toBeNull()
    })

    it('clears any existing error', async () => {
      const { result } = renderHook(() => useFileUpload())
      const invalidFile = createMockFile('document.pdf', 1024, 'application/pdf')

      await act(async () => {
        result.current.handleFileDrop([invalidFile])
      })

      await waitFor(() => {
        expect(result.current.error).not.toBeNull()
      })

      act(() => {
        result.current.clearFile()
      })

      expect(result.current.error).toBeNull()
    })

    it('can be called when no file is uploaded', () => {
      const { result } = renderHook(() => useFileUpload())

      // Should not throw
      act(() => {
        result.current.clearFile()
      })

      expect(result.current.uploadedFile).toBeNull()
      expect(result.current.error).toBeNull()
    })
  })

  describe('handleFileSelect', () => {
    it('processes files from input change event', async () => {
      const { result } = renderHook(() => useFileUpload())
      const mockFile = createMockFile('input.csv', 1024, 'text/csv')

      const mockEvent = {
        target: {
          files: [mockFile],
        },
      } as unknown as React.ChangeEvent<HTMLInputElement>

      await act(async () => {
        result.current.handleFileSelect(mockEvent)
      })

      await waitFor(() => {
        expect(result.current.uploadedFile).not.toBeNull()
      })

      expect(result.current.uploadedFile?.name).toBe('input.csv')
    })

    it('handles empty file list', async () => {
      const { result } = renderHook(() => useFileUpload())

      const mockEvent = {
        target: {
          files: null,
        },
      } as unknown as React.ChangeEvent<HTMLInputElement>

      await act(async () => {
        result.current.handleFileSelect(mockEvent)
      })

      expect(result.current.uploadedFile).toBeNull()
      expect(result.current.error).toBeNull()
    })
  })

  describe('handleFileDrop', () => {
    it('processes files from FileList', async () => {
      const { result } = renderHook(() => useFileUpload())
      const mockFile = createMockFile('dropped.csv', 1024, 'text/csv')

      const mockFileList = {
        0: mockFile,
        length: 1,
        item: (index: number) => (index === 0 ? mockFile : null),
        [Symbol.iterator]: function* () {
          yield mockFile
        },
      } as unknown as FileList

      await act(async () => {
        result.current.handleFileDrop(mockFileList)
      })

      await waitFor(() => {
        expect(result.current.uploadedFile).not.toBeNull()
      })

      expect(result.current.uploadedFile?.name).toBe('dropped.csv')
    })

    it('only processes the first file when multiple are dropped', async () => {
      const { result } = renderHook(() => useFileUpload())
      const file1 = createMockFile('first.csv', 1024, 'text/csv')
      const file2 = createMockFile('second.csv', 2048, 'text/csv')

      await act(async () => {
        result.current.handleFileDrop([file1, file2])
      })

      await waitFor(() => {
        expect(result.current.uploadedFile).not.toBeNull()
      })

      expect(result.current.uploadedFile?.name).toBe('first.csv')
    })

    it('handles empty file array', async () => {
      const { result } = renderHook(() => useFileUpload())

      await act(async () => {
        result.current.handleFileDrop([])
      })

      expect(result.current.uploadedFile).toBeNull()
      expect(result.current.error).toBeNull()
    })
  })

  describe('column name sanitization', () => {
    it('sanitizes HTML characters in column names', async () => {
      // Create custom MockFileReader for this test
      class HtmlColumnMockFileReader {
        result: string | null = null
        onload: ((event: ProgressEvent<FileReader>) => void) | null = null
        onerror: ((event: ProgressEvent<FileReader>) => void) | null = null

        readAsText() {
          setTimeout(() => {
            if (this.onload) {
              this.result = '<script>alert("xss")</script>, Column&Name, "Quoted"\n'
              this.onload({ target: this } as ProgressEvent<FileReader>)
            }
          }, 0)
        }
      }

      // @ts-expect-error - Mocking FileReader
      global.FileReader = HtmlColumnMockFileReader

      const { result } = renderHook(() => useFileUpload())
      const mockFile = createMockFile('test.csv', 1024, 'text/csv')

      await act(async () => {
        result.current.handleFileDrop([mockFile])
      })

      await waitFor(() => {
        expect(result.current.uploadedFile).not.toBeNull()
      })

      // Verify HTML is escaped
      expect(result.current.uploadedFile?.columns[0]).toBe(
        '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;'
      )
      expect(result.current.uploadedFile?.columns[1]).toBe('Column&amp;Name')
    })
  })
})
