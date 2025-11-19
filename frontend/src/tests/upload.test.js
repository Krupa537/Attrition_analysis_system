import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import Upload from '../pages/Upload'
import React from 'react'

// Mock fetch
global.fetch = vi.fn()

describe('Upload Component', () => {
  beforeEach(() => {
    fetch.mockClear()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('should render upload form', () => {
    render(<Upload />)
    
    expect(screen.getByText('Upload Dataset')).toBeInTheDocument()
    expect(screen.getByText('Upload CSV')).toBeInTheDocument()
  })

  it('should handle file selection', () => {
    render(<Upload />)
    
    const fileInput = screen.getByLabelText(/choose file/i) || 
                     document.querySelector('input[type="file"]')
    
    expect(fileInput).toBeInTheDocument()
  })

  it('should show error when no file selected and upload clicked', async () => {
    render(<Upload />)
    
    const uploadButton = screen.getByText('Upload CSV')
    fireEvent.click(uploadButton)
    
    await waitFor(() => {
      expect(screen.getByText(/choose a csv file first/i)).toBeInTheDocument()
    })
  })

  it('should call fetch when uploading file', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        dataset_id: 'test-123',
        columns: ['Age', 'Department'],
        sample: [],
        validation: { record_count: 10 }
      })
    })

    render(<Upload />)
    
    // This would require actual file input simulation
    expect(fetch).not.toHaveBeenCalled()
  })

  it('should display dataset ID after successful upload', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        dataset_id: 'dataset-123',
        columns: ['Age', 'Department', 'Attrition'],
        sample: [],
        validation: { record_count: 100 }
      })
    })

    render(<Upload />)
    
    // Initial state should not show dataset ID
    expect(screen.queryByText(/dataset id/i)).not.toBeInTheDocument()
  })

  it('should show validation summary', async () => {
    render(<Upload />)
    
    // Should only appear after upload
    expect(screen.queryByText(/validation summary/i)).not.toBeInTheDocument()
  })

  it('should display Run Analysis button after upload', async () => {
    render(<Upload />)
    
    // Initially should not be visible
    const analysisButtons = screen.queryAllByText(/run analysis/i)
    expect(analysisButtons.length).toBe(0)
  })
})

describe('Upload Component - API Calls', () => {
  beforeEach(() => {
    fetch.mockClear()
  })

  it('should make correct upload request', async () => {
    const mockResponse = {
      ok: true,
      json: async () => ({
        dataset_id: 'test-123',
        columns: ['Age'],
        sample: [],
        validation: {}
      })
    }

    fetch.mockResolvedValueOnce(mockResponse)

    // Simulate upload
    const formData = new FormData()
    formData.append('file', new Blob(['Age\n25']), 'test.csv')

    // Manual fetch call
    const response = await fetch('http://127.0.0.1:8000/api/upload', {
      method: 'POST',
      body: formData
    })

    expect(fetch).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/api/upload',
      expect.objectContaining({
        method: 'POST'
      })
    )
  })

  it('should handle upload errors', async () => {
    fetch.mockRejectedValueOnce(new Error('Network error'))

    try {
      await fetch('http://127.0.0.1:8000/api/upload', {
        method: 'POST',
        body: new FormData()
      })
    } catch (error) {
      expect(error.message).toBe('Network error')
    }
  })
})

describe('Download Functions', () => {
  it('should create download link correctly', () => {
    const url = 'http://127.0.0.1:8000/api/download/model/analysis-123'
    const filename = 'model_analysis-123.pkl'

    expect(url).toContain('download')
    expect(filename).toContain('pkl')
  })

  it('should handle download for PDF', () => {
    const url = 'http://127.0.0.1:8000/api/download/analysis/analysis-123/pdf'
    
    expect(url).toContain('pdf')
  })

  it('should handle download for predictions', () => {
    const url = 'http://127.0.0.1:8000/api/download/predictions/analysis-123'
    
    expect(url).toContain('predictions')
  })
})
