import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { FileDropZone } from '@/components/features/discovery/FileDropZone'

describe('FileDropZone', () => {
  it('renders drop zone with instructions', () => {
    render(<FileDropZone onFileDrop={vi.fn()} />)

    expect(screen.getByText(/drag and drop/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /browse/i })).toBeInTheDocument()
  })

  it('accepts CSV files', async () => {
    const onFileDrop = vi.fn()
    render(<FileDropZone onFileDrop={onFileDrop} accept={['.csv', '.xlsx']} />)

    const file = new File(['content'], 'data.csv', { type: 'text/csv' })
    const dropzone = screen.getByTestId('file-dropzone')

    fireEvent.drop(dropzone, { dataTransfer: { files: [file] } })

    await waitFor(() => {
      expect(onFileDrop).toHaveBeenCalledWith(file)
    })
  })

  it('rejects unsupported file types', async () => {
    const onFileDrop = vi.fn()
    const onError = vi.fn()
    render(<FileDropZone onFileDrop={onFileDrop} onError={onError} accept={['.csv']} />)

    const file = new File(['content'], 'report.pdf', { type: 'application/pdf' })
    const dropzone = screen.getByTestId('file-dropzone')

    fireEvent.drop(dropzone, { dataTransfer: { files: [file] } })

    await waitFor(() => {
      expect(onFileDrop).not.toHaveBeenCalled()
      expect(onError).toHaveBeenCalled()
    })
  })

  it('shows drag over state', () => {
    render(<FileDropZone onFileDrop={vi.fn()} />)

    const dropzone = screen.getByTestId('file-dropzone')
    fireEvent.dragEnter(dropzone)

    expect(dropzone).toHaveClass('border-primary')
  })

  it('shows file size limit', () => {
    render(<FileDropZone onFileDrop={vi.fn()} maxSizeMB={10} />)

    expect(screen.getByText(/10 MB/i)).toBeInTheDocument()
  })

  it('shows uploading state', () => {
    render(<FileDropZone onFileDrop={vi.fn()} isUploading={true} progress={50} />)

    expect(screen.getByRole('progressbar')).toBeInTheDocument()
    expect(screen.getByText('50%')).toBeInTheDocument()
  })
})
