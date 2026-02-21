import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Paper,
  Typography,
} from '@mui/material'
import { useState } from 'react'

interface BatchTabProps {
  apiUrl: string
  apiKey: string
}

export function BatchTab({ apiUrl, apiKey }: BatchTabProps) {
  const [batchFile, setBatchFile] = useState<File | null>(null)
  const [batchLoading, setBatchLoading] = useState(false)
  const [batchError, setBatchError] = useState('')
  const [batchDownloadUrl, setBatchDownloadUrl] = useState('')
  const [batchPreview, setBatchPreview] = useState<string[]>([])

  const handleBatch = async () => {
    if (!batchFile) {
      setBatchError('Select a CSV file first')
      return
    }
    setBatchError('')
    setBatchDownloadUrl('')
    setBatchPreview([])
    setBatchLoading(true)
    try {
      const formData = new FormData()
      formData.append('file', batchFile)
      const requestHeaders: Record<string, string> = {}
      if (apiKey.trim()) {
        requestHeaders['x-api-key'] = apiKey.trim()
      }
      const response = await fetch(`${apiUrl}/v1/batch`, {
        method: 'POST',
        headers: requestHeaders,
        body: formData,
      })
      if (!response.ok) {
        const text = await response.text()
        throw new Error(text || 'Request failed')
      }
      const text = await response.text()
      const lines = text.split(/\r?\n/).filter(Boolean)
      setBatchPreview(lines.slice(0, 6))
      const blob = new Blob([text], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      setBatchDownloadUrl(url)
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Request failed'
      setBatchError(message)
    } finally {
      setBatchLoading(false)
    }
  }

  return (
    <Box display="grid" gap={2}>
      <Button variant="outlined" component="label">
        Select CSV
        <input
          type="file"
          accept=".csv"
          hidden
          onChange={(event) => {
            const file = event.target.files?.[0] ?? null
            setBatchFile(file)
          }}
        />
      </Button>
      {batchFile && (
        <Typography variant="body2" color="text.secondary">
          Selected: {batchFile.name}
        </Typography>
      )}
      <Box display="flex" alignItems="center" gap={2}>
        <Button
          variant="contained"
          onClick={handleBatch}
          disabled={!batchFile || batchLoading}
        >
          Run Batch
        </Button>
        {batchLoading && <CircularProgress size={24} />}
      </Box>
      {batchError && <Alert severity="error">{batchError}</Alert>}
      {batchPreview.length > 0 && (
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="subtitle1" gutterBottom>
            Preview
          </Typography>
          {batchPreview.map((line, index) => (
            <Typography variant="body2" key={`${line}-${index}`}>
              {line}
            </Typography>
          ))}
        </Paper>
      )}
      {batchDownloadUrl && (
        <Button
          variant="outlined"
          href={batchDownloadUrl}
          download={`predictions_${batchFile?.name ?? 'output.csv'}`}
        >
          Download Results
        </Button>
      )}
    </Box>
  )
}
