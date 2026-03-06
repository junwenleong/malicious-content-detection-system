import { AppBar, Container, Typography, Chip, Stack } from "@mui/material";

export function Header() {
  return (
    <AppBar position="static" elevation={0}>
      <Container maxWidth="lg" sx={{ py: 3 }}>
        <Stack direction="row" alignItems="center" spacing={2} mb={1}>
          <Typography variant="h4" fontWeight={700} color="text.primary">
            Malicious Content Detection
          </Typography>
          <Chip label="v1.0" size="small" color="primary" variant="outlined" />
        </Stack>
        <Typography variant="body1" color="text.secondary">
          Content Safety Analysis Platform
        </Typography>
      </Container>
    </AppBar>
  );
}
