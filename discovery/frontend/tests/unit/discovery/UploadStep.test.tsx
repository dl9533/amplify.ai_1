import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { UploadStep } from '@/pages/discovery/UploadStep'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

const renderWithRouter = (ui: React.ReactElement) => {
  return render(
    <MemoryRouter initialEntries={['/discovery/session-1/upload']}>
      <Routes>
        <Route path="/discovery/:sessionId/upload" element={ui} />
      </Routes>
    </MemoryRouter>
  )
}

describe('UploadStep', () => {
  it('renders upload instructions', () => {
    renderWithRouter(<UploadStep />)

    expect(screen.getByText(/upload your organization data/i)).toBeInTheDocument()
    expect(screen.getByText(/csv or xlsx/i)).toBeInTheDocument()
  })

  it('shows file drop zone', () => {
    renderWithRouter(<UploadStep />)

    expect(screen.getByRole('button', { name: /browse files/i })).toBeInTheDocument()
  })

  it('displays uploaded file info after upload', async () => {
    renderWithRouter(<UploadStep />)

    const file = new File(['name,role\nJohn,Engineer'], 'data.csv', { type: 'text/csv' })
    const dropzone = screen.getByTestId('file-dropzone')

    // Simulate file drop
    fireEvent.drop(dropzone, {
      dataTransfer: { files: [file] },
    })

    await waitFor(() => {
      expect(screen.getByText('data.csv')).toBeInTheDocument()
    })
  })

  it('shows column mapping preview after upload', async () => {
    renderWithRouter(<UploadStep />)

    const file = new File(['name,role\nJohn,Engineer'], 'data.csv', { type: 'text/csv' })
    const dropzone = screen.getByTestId('file-dropzone')

    fireEvent.drop(dropzone, {
      dataTransfer: { files: [file] },
    })

    // After file is uploaded, should show mapping preview
    await waitFor(() => {
      expect(screen.getByText(/detected columns/i)).toBeInTheDocument()
    })
  })

  it('enables next step button when upload complete', async () => {
    renderWithRouter(<UploadStep />)

    // Initially disabled
    const continueButton = screen.getByRole('button', { name: /continue/i })
    expect(continueButton).toBeDisabled()

    // Upload file
    const file = new File(['name,role\nJohn,Engineer'], 'data.csv', { type: 'text/csv' })
    const dropzone = screen.getByTestId('file-dropzone')
    fireEvent.drop(dropzone, { dataTransfer: { files: [file] } })

    // Should be enabled after upload
    await waitFor(() => {
      expect(continueButton).not.toBeDisabled()
    })
  })
})
