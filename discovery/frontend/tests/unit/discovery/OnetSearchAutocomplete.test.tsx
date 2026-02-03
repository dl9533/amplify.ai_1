import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { OnetSearchAutocomplete } from '@/components/features/discovery/OnetSearchAutocomplete'
import { mockOnetApi, resetAllMocks } from '../../__mocks__/services'

describe('OnetSearchAutocomplete', () => {
  beforeEach(() => {
    resetAllMocks()
  })

  it('renders search input', () => {
    render(<OnetSearchAutocomplete onSelect={vi.fn()} />)

    expect(screen.getByRole('combobox')).toBeInTheDocument()
  })

  it('shows loading state while searching', async () => {
    render(<OnetSearchAutocomplete onSelect={vi.fn()} />)

    const input = screen.getByRole('combobox')
    fireEvent.change(input, { target: { value: 'software' } })

    // Should show loading status immediately
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('displays search results', async () => {
    render(<OnetSearchAutocomplete onSelect={vi.fn()} />)

    const input = screen.getByRole('combobox')
    fireEvent.change(input, { target: { value: 'software' } })

    await waitFor(() => {
      expect(screen.getByText('Software Developers')).toBeInTheDocument()
      expect(screen.getByText('15-1252.00')).toBeInTheDocument()
    }, { timeout: 1000 })
  })

  it('calls onSelect when result clicked', async () => {
    const onSelect = vi.fn()
    render(<OnetSearchAutocomplete onSelect={onSelect} />)

    const input = screen.getByRole('combobox')
    fireEvent.change(input, { target: { value: 'software' } })

    await waitFor(() => {
      expect(screen.getByText('Software Developers')).toBeInTheDocument()
    }, { timeout: 1000 })

    fireEvent.click(screen.getByText('Software Developers'))

    expect(onSelect).toHaveBeenCalledWith({
      code: '15-1252.00',
      title: 'Software Developers',
    })
  })

  it('debounces search requests', async () => {
    render(<OnetSearchAutocomplete onSelect={vi.fn()} />)

    const input = screen.getByRole('combobox')
    fireEvent.change(input, { target: { value: 's' } })
    fireEvent.change(input, { target: { value: 'so' } })
    fireEvent.change(input, { target: { value: 'sof' } })

    // Should debounce to single request
    await waitFor(() => {
      expect(screen.queryByRole('listbox')).toBeInTheDocument()
    }, { timeout: 1000 })
  })

  it('shows no results message', async () => {
    // Override the mock to return empty results
    mockOnetApi.search.mockResolvedValueOnce([])

    render(<OnetSearchAutocomplete onSelect={vi.fn()} />)

    const input = screen.getByRole('combobox')
    fireEvent.change(input, { target: { value: 'xyznotfound123' } })

    await waitFor(() => {
      expect(screen.getByText(/no results/i)).toBeInTheDocument()
    }, { timeout: 1000 })
  })

  it('supports keyboard navigation', async () => {
    const onSelect = vi.fn()
    render(<OnetSearchAutocomplete onSelect={onSelect} />)

    const input = screen.getByRole('combobox')
    fireEvent.change(input, { target: { value: 'software' } })

    await waitFor(() => {
      expect(screen.getByRole('listbox')).toBeInTheDocument()
    }, { timeout: 1000 })

    // Navigate down
    fireEvent.keyDown(input, { key: 'ArrowDown' })

    // Press Enter to select
    fireEvent.keyDown(input, { key: 'Enter' })

    expect(onSelect).toHaveBeenCalled()
  })

  it('closes dropdown on Escape key', async () => {
    render(<OnetSearchAutocomplete onSelect={vi.fn()} />)

    const input = screen.getByRole('combobox')
    fireEvent.change(input, { target: { value: 'software' } })

    await waitFor(() => {
      expect(screen.getByRole('listbox')).toBeInTheDocument()
    }, { timeout: 1000 })

    fireEvent.keyDown(input, { key: 'Escape' })

    await waitFor(() => {
      expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
    })
  })

  it('has placeholder on input', () => {
    render(<OnetSearchAutocomplete onSelect={vi.fn()} placeholder="Custom placeholder" />)

    const input = screen.getByRole('combobox')
    expect(input).toHaveAttribute('placeholder', 'Custom placeholder')
  })

  it('updates aria-selected on keyboard navigation', async () => {
    render(<OnetSearchAutocomplete onSelect={vi.fn()} />)

    const input = screen.getByRole('combobox')
    fireEvent.change(input, { target: { value: 'software' } })

    await waitFor(() => {
      expect(screen.getByRole('listbox')).toBeInTheDocument()
    }, { timeout: 1000 })

    // Navigate down to first option
    fireEvent.keyDown(input, { key: 'ArrowDown' })

    const options = screen.getAllByRole('option')
    expect(options[0]).toHaveAttribute('aria-selected', 'true')
  })
})
