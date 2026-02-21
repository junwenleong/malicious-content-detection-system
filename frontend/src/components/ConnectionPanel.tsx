import { Alert, Box, Paper, TextField, Typography } from '@mui/material'

interface ConnectionPanelProps {
  apiUrl: string
  setApiUrl: (url: string) => void
  apiKey: string
  setApiKey: (key: string) => void
  healthStatus: 'unknown' | 'ok' | 'error'
  healthMessage: string
}

export function ConnectionPanel({
  apiUrl,
  setApiUrl,
  apiKey,
  setApiKey,
  healthStatus,
  healthMessage,
}: ConnectionPanelProps) {
  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        Connection
      </Typography>
      <Box display="grid" gap={2} gridTemplateColumns={{ xs: '1fr', md: '2fr 1fr' }}>
        <TextField
          label="API Base URL"
          value={apiUrl}
          onChange={(event) => setApiUrl(event.target.value)}
          fullWidth
        />
        <TextField
          label="API Key"
          value={apiKey}
          onChange={(event) => setApiKey(event.target.value)}
          type="password"
          fullWidth
        />
      </Box>
      <Box mt={2}>
        {healthStatus === 'ok' && (
          <Alert severity="success">API healthy ({healthMessage})</Alert>
        )}
        {healthStatus === 'error' && (
          <Alert severity="error">API unreachable ({healthMessage || 'error'})</Alert>
        )}
      </Box>
    </Paper>
  )
}
