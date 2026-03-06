import { useEffect, useMemo, useState } from "react";
import {
  Box,
  Container,
  CssBaseline,
  IconButton,
  Paper,
  Tab,
  Tabs,
  ThemeProvider,
  Tooltip,
  useMediaQuery,
} from "@mui/material";
import DarkModeIcon from "@mui/icons-material/DarkMode";
import LightModeIcon from "@mui/icons-material/LightMode";
import { Header } from "./components/Header";

import { ConnectionPanel } from "./components/ConnectionPanel";
import { AnalyzeTab } from "./components/AnalyzeTab";
import { BatchTab } from "./components/BatchTab";
import { buildTheme } from "./theme";

const defaultApiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const defaultApiKey = import.meta.env.VITE_DEFAULT_API_KEY ?? "";

function App() {
  const prefersDarkMode = useMediaQuery("(prefers-color-scheme: dark)");

  // Manual override stored in localStorage; falls back to OS preference
  const [modeOverride, setModeOverride] = useState<"light" | "dark" | null>(
    () => {
      const stored = localStorage.getItem("color_mode");
      return stored === "light" || stored === "dark" ? stored : null;
    },
  );

  const mode = modeOverride ?? (prefersDarkMode ? "dark" : "light");
  const theme = useMemo(() => buildTheme(mode), [mode]);

  const toggleMode = () => {
    const next = mode === "dark" ? "light" : "dark";
    setModeOverride(next);
    localStorage.setItem("color_mode", next);
  };

  const [tab, setTab] = useState(0);
  const [apiUrl, setApiUrl] = useState(
    () => localStorage.getItem("api_url") ?? defaultApiUrl,
  );
  const [apiKey, setApiKey] = useState(
    () => localStorage.getItem("api_key") ?? defaultApiKey,
  );
  const [healthStatus, setHealthStatus] = useState<"unknown" | "ok" | "error">(
    "unknown",
  );
  const [healthMessage, setHealthMessage] = useState("");

  useEffect(() => {
    localStorage.setItem("api_url", apiUrl);
  }, [apiUrl]);

  useEffect(() => {
    localStorage.setItem("api_key", apiKey);
  }, [apiKey]);

  useEffect(() => {
    let isMounted = true;
    const loadHealth = async () => {
      setHealthStatus("unknown");
      setHealthMessage("");
      try {
        const response = await fetch(`${apiUrl}/health`);
        if (!isMounted) return;
        if (response.ok) {
          const data = await response.json();
          setHealthStatus("ok");
          setHealthMessage(data.status ?? "healthy");
        } else {
          setHealthStatus("error");
          setHealthMessage("unreachable");
        }
      } catch {
        if (!isMounted) return;
        setHealthStatus("error");
        setHealthMessage("unreachable");
      }
    };
    loadHealth();
    return () => {
      isMounted = false;
    };
  }, [apiUrl]);

  const headers = useMemo(() => {
    const baseHeaders: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (apiKey.trim()) {
      baseHeaders["x-api-key"] = apiKey.trim();
    }
    return baseHeaders;
  }, [apiKey]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Header />
      <Container maxWidth="lg" sx={{ pb: 6 }}>
        <ConnectionPanel
          apiUrl={apiUrl}
          setApiUrl={setApiUrl}
          apiKey={apiKey}
          setApiKey={setApiKey}
          healthStatus={healthStatus}
          healthMessage={healthMessage}
        />

        <Paper sx={{ p: 0 }}>
          <Tabs
            value={tab}
            onChange={(_, value: number) => setTab(value)}
            indicatorColor="primary"
            textColor="primary"
          >
            <Tab label="Analyze Text" />
            <Tab label="Batch Upload" />
          </Tabs>
          <Box p={3}>
            {tab === 0 && <AnalyzeTab apiUrl={apiUrl} headers={headers} />}
            {tab === 1 && <BatchTab apiUrl={apiUrl} apiKey={apiKey} />}
          </Box>
        </Paper>
      </Container>

      {/* Floating mode toggle — bottom-right corner */}
      <Tooltip title={`Switch to ${mode === "dark" ? "light" : "dark"} mode`}>
        <IconButton
          onClick={toggleMode}
          aria-label={`Switch to ${mode === "dark" ? "light" : "dark"} mode`}
          sx={{
            position: "fixed",
            bottom: 24,
            right: 24,
            bgcolor: "background.paper",
            border: "1px solid",
            borderColor: "divider",
            boxShadow: 3,
            "&:hover": { bgcolor: "action.hover" },
          }}
          size="large"
        >
          {mode === "dark" ? <LightModeIcon /> : <DarkModeIcon />}
        </IconButton>
      </Tooltip>
    </ThemeProvider>
  );
}

export default App;
