import { render, screen, fireEvent, within } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ColumnMappingPreview } from '@/components/features/discovery/ColumnMappingPreview'

const schema = {
  columns: ['Name', 'Job Title', 'Department', 'Location'],
  sampleRows: [
    ['John Smith', 'Software Engineer', 'Engineering', 'NYC'],
    ['Jane Doe', 'Data Analyst', 'Analytics', 'SF'],
  ],
}

const mappings = {
  role: 'Job Title',
  department: 'Department',
  geography: 'Location',
}

describe('ColumnMappingPreview', () => {
  it('renders detected columns', () => {
    render(<ColumnMappingPreview schema={schema} mappings={mappings} onMappingChange={vi.fn()} />)

    const table = screen.getByRole('table')
    const headers = within(table).getAllByRole('columnheader')
    expect(headers).toHaveLength(4)
    expect(headers[0]).toHaveTextContent('Name')
    expect(headers[1]).toHaveTextContent('Job Title')
    expect(headers[2]).toHaveTextContent('Department')
  })

  it('shows sample data rows', () => {
    render(<ColumnMappingPreview schema={schema} mappings={mappings} onMappingChange={vi.fn()} />)

    expect(screen.getByText('John Smith')).toBeInTheDocument()
    expect(screen.getByText('Software Engineer')).toBeInTheDocument()
  })

  it('highlights mapped columns', () => {
    render(<ColumnMappingPreview schema={schema} mappings={mappings} onMappingChange={vi.fn()} />)

    const table = screen.getByRole('table')
    const headers = within(table).getAllByRole('columnheader')
    // Job Title is mapped to role, so it should be highlighted
    expect(headers[1]).toHaveClass('bg-primary/10')
  })

  it('allows changing column mapping', () => {
    const onMappingChange = vi.fn()
    render(<ColumnMappingPreview schema={schema} mappings={mappings} onMappingChange={onMappingChange} />)

    const select = screen.getByLabelText(/role column/i)
    fireEvent.change(select, { target: { value: 'Name' } })

    expect(onMappingChange).toHaveBeenCalledWith({ ...mappings, role: 'Name' })
  })

  it('shows required column indicators', () => {
    render(<ColumnMappingPreview schema={schema} mappings={{}} onMappingChange={vi.fn()} />)

    expect(screen.getByText(/role.*required/i)).toBeInTheDocument()
  })
})
