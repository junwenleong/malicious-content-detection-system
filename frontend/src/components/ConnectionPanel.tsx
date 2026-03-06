import {
  Alert,
  Box,
  Button,
  Chip,
  Collapse,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";
import SettingsIcon from "@mui/icons-material/TuneRounded";

interface ConnectionPanelProps {
  apiUrl: string;
  setApiUrl: (url: string) => void;
  apiKey: string;
  setApiKey: (key: string) => void;
  healthStatus: "unknown" | "ok" | "error";
  healthMessage: string;
}

const STATUS_CHIP: Record<
  string,
  { label: string; color: "success" | "error" | "default" }
> = {
  ok: { label: "Connected", color: "success" },
  error: { label: "Disconnected", color: "error" },
  unknown: { label: "Checking…", color: "default" },
};

export function ConnectionPanel({
  apiUrl,
  setApiUrl,
  apiKey,
  setApiKey,
  healthStatus,
  healthMessage,
}: ConnectionPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const chip = STATUS_CHIP[healthStatus];

  return (
    <Paper sx={{ p: 0, overflow: "hidden" }}>
      {/* Header row */}
      <Stack
        direction="row"
        alignItems="center"
        justifyContent="space-between"
        sx={{ px: 2.5, py: 1.5 }}
      >
        <Stack direction="row" alignItems="center" spacing={1.5}>
          <SettingsIcon sx={{ fontSize: 16, color: "text.secondary" }} />
          <Typography variant="body2" fontWeight={600} color="text.primary">
            API Connection
          </Typography>
          <Chip
            label={chip.label}
            color={chip.color}
            size="small"
            variant="outlined"
          />
        </Stack>
        <Button
          size="small"
          onClick={() => setExpanded(!expanded)}
          aria-expanded={expanded}
          aria-controls="connection-settings-panel"
          sx={{ color: "text.secondary", fontSize: "0.75rem" }}
        >
          {expanded ? "Done" : "Configure"}
        </Button>
      </Stack>

      <Collapse in={expanded} id="connection-settings-panel">
        <Box
          component="form"
          autoComplete="off"
          onSubmit={(e) => e.preventDefault()}
          sx={{
            display: "grid",
            gap: 2,
            gridTemplateColumns: { xs: "1fr", md: "2fr 1fr" },
            px: 2.5,
            pb: 2.5,
          }}
        >
          <TextField
            label="API Base URL"
            value={apiUrl}
            onChange={(e) => setApiUrl(e.target.value)}
            fullWidth
            size="small"
            helperText="e.g. http://localhost:8000"
            inputProps={{ autoComplete: "off" }}
          />
          <TextField
            label="API Key"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            type="password"
            fullWidth
            size="small"
            helperText="Required for authentication"
            inputProps={{ autoComplete: "new-password" }}
          />
          {healthStatus !== "unknown" && (
            <Box sx={{ gridColumn: "1 / -1" }}>
              {healthStatus === "ok" ? (
                <Alert severity="success" sx={{ py: 0.5 }}>
                  API healthy — {healthMessage}
                </Alert>
              ) : (
                <Alert severity="error" sx={{ py: 0.5 }}>
                  API unreachable ({healthMessage || "connection refused"})
                </Alert>
              )}
            </Box>
          )}
        </Box>
      </Collapse>
    </Paper>
  );
}
