import { AppBar, Container, Typography } from '@mui/material'

export function Header() {
  return (
    <AppBar position="static" color="transparent" elevation={0}>
      <Container maxWidth="lg" sx={{ py: 3 }}>
        <Typography variant="h4" fontWeight={600}>
          Malicious Content Detection
        </Typography>
        <Typography variant="body1" color="text.secondary">
          React + FastAPI, decoupled with secure defaults
        </Typography>
      </Container>
    </AppBar>
  )
}
