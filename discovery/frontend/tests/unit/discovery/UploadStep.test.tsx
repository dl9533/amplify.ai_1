import { screen, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeEach } from 'vitest'
import { UploadStep } from '@/pages/discovery/UploadStep'
import { renderWithRouter } from '../../test-utils'
import { resetAllMocks } from '../../__mocks__/services'

describe('UploadStep', () => {
  beforeEach(() => {
    resetAllMocks()
  })

  it('renders upload instructions', async () => {
    renderWithRouter(<UploadStep />, {
      route: '/discovery/session-1/upload',
      routePath: '/discovery/:sessionId/upload',
    })

    await waitFor(() => {
      expect(screen.getByText(/upload workforce data/i)).toBeInTheDocument()
    })
  })

  it('shows file type information', async () => {
    renderWithRouter(<UploadStep />, {
      route: '/discovery/session-1/upload',
      routePath: '/discovery/:sessionId/upload',
    })

    await waitFor(() => {
      expect(screen.getByText(/csv/i)).toBeInTheDocument()
      expect(screen.getByText(/excel/i)).toBeInTheDocument()
    })
  })

  it('renders drag and drop area', async () => {
    renderWithRouter(<UploadStep />, {
      route: '/discovery/session-1/upload',
      routePath: '/discovery/:sessionId/upload',
    })

    await waitFor(() => {
      expect(screen.getByText(/drag and drop/i)).toBeInTheDocument()
    })
  })

  it('shows browse option', async () => {
    renderWithRouter(<UploadStep />, {
      route: '/discovery/session-1/upload',
      routePath: '/discovery/:sessionId/upload',
    })

    await waitFor(() => {
      expect(screen.getByText(/browse/i)).toBeInTheDocument()
    })
  })

  it('has file input for uploading', async () => {
    const { container } = renderWithRouter(<UploadStep />, {
      route: '/discovery/session-1/upload',
      routePath: '/discovery/:sessionId/upload',
    })

    await waitFor(() => {
      const fileInput = container.querySelector('input[type="file"]')
      expect(fileInput).toBeInTheDocument()
      expect(fileInput).toHaveAttribute('accept', '.csv,.xlsx,.xls')
    })
  })
})
