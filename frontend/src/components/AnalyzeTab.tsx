import { Alert, Box, Button, Chip, CircularProgress, Paper, TextField, Typography } from '@mui/material'
import { useState } from 'react'
import type { PredictResponse } from '../types'

interface AnalyzeTabProps {
  apiUrl: string
  headers: Record<string, string>
}

export function AnalyzeTab({ apiUrl, headers }: AnalyzeTabProps) {
  const [textInput, setTextInput] = useState('')
  const [predictLoading, setPredictLoading] = useState(false)
  const [predictError, setPredictError] = useState('')
  const [predictData, setPredictData] = useState<PredictResponse | null>(null)

  const handleAnalyze = async () => {
    setPredictError('')
    setPredictData(null)
    setPredictLoading(true)
    try {
      const response = await fetch(`${apiUrl}/v1/predict`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ texts: [textInput] }),
      })
      if (!response.ok) {
        const text = await response.text()
        throw new Error(text || 'Request failed')
      }
      const data = (await response.json()) as PredictResponse
      setPredictData(data)
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Request failed'
      setPredictError(message)
    } finally {
      setPredictLoading(false)
    }
  }

  return (
    <Box display="grid" gap={2}>
      <TextField
        label="Text to analyze"
        multiline
        minRows={4}
        value={textInput}
        onChange={(event) => setTextInput(event.target.value)}
        fullWidth
      />
      <Box display="flex" alignItems="center" gap={2}>
        <Button
          variant="contained"
          onClick={handleAnalyze}
          disabled={!textInput.trim() || predictLoading}
        >
          Analyze
        </Button>
        {predictLoading && <CircularProgress size={24} />}
      </Box>
      {predictError && <Alert severity="error">{predictError}</Alert>}
      {predictData && (
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="subtitle1" gutterBottom>
            Results
          </Typography>
          {predictData.metadata?.model_version && (
            <Typography variant="body2" color="text.secondary">
              Model: {predictData.metadata.model_version}
            </Typography>
          )}
          <Box display="grid" gap={1}>
            {predictData.predictions.map((prediction, index) => (
              <Box key={`${prediction.text}-${index}`}>
                <Typography fontWeight={600}>{prediction.label}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Probability: {prediction.probability_malicious.toFixed(4)} | Threshold:{' '}
                  {prediction.threshold}
                </Typography>
                <Box display="flex" gap={1}>
                  <Chip
                    label={`Risk: ${prediction.risk_level}`}
                    color={
                      prediction.risk_level === 'HIGH'
                        ? 'error'
                        : prediction.risk_level === 'MEDIUM'
                        ? 'warning'
                        : 'success'
                    }
                    size="small"
                  />
                  <Chip
                    label={`Action: ${prediction.recommended_action}`}
                    color={
                      prediction.recommended_action === 'BLOCK'
                        ? 'error'
                        : prediction.recommended_action === 'REVIEW'
                        ? 'warning'
                        : 'success'
                    }
                    size="small"
                  />
                </Box>
                <Typography variant="body2">{prediction.text}</Typography>
              </Box>
            ))}
          </Box>
        </Paper>
      )}
    </Box>
  )
}
