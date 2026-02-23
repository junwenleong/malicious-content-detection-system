import { Alert, Box, Paper, TextField, Typography, Collapse, Chip, Button } from '@mui/material'
import { useState } from 'react'

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
  const [expanded, setExpanded] = useState(false);

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={expanded ? 2 : 0}>
        <Box display="flex" alignItems="center" gap={2}>
            <Typography variant="h6">
                Connection Settings
            </Typography>
            {healthStatus === 'ok' && (
                <Chip label="Connected" color="success" size="small" variant="outlined" />
            )}
            {healthStatus === 'error' && (
                <Chip label="Disconnected" color="error" size="small" variant="outlined" />
            )}
        </Box>
        <Button onClick={() => setExpanded(!expanded)} size="small">
            {expanded ? 'Hide' : 'Configure'}
        </Button>
      </Box>
      
      <Collapse in={expanded}>
        <Box display="grid" gap={2} gridTemplateColumns={{ xs: '1fr', md: '2fr 1fr' }}>
            <TextField
            label="API Base URL"
            value={apiUrl}
            onChange={(event) => setApiUrl(event.target.value)}
            fullWidth
            helperText="e.g. http://localhost:8000"
            />
            <TextField
            label="API Key (Optional)"
            value={apiKey}
            onChange={(event) => setApiKey(event.target.value)}
            type="password"
            fullWidth
            helperText="Leave empty for local dev"
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
      </Collapse>
    </Paper>
  )
}
