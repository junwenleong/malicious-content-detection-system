import { useEffect, useMemo, useState } from "react";
import {
  Box,
  Container,
  CssBaseline,
  Paper,
  Tab,
  Tabs,
  ThemeProvider,
  createTheme,
  useMediaQuery,
} from "@mui/material";
import { Header } from "./components/Header";
import { ConnectionPanel } from "./components/ConnectionPanel";
import { AnalyzeTab } from "./components/AnalyzeTab";
import { BatchTab } from "./components/BatchTab";

const defaultApiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const defaultApiKey = "dev-secret-key-123";

function App() {
  const prefersDarkMode = useMediaQuery("(prefers-color-scheme: dark)");
  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode: prefersDarkMode ? "dark" : "light",
        },
      }),
    [prefersDarkMode],
  );

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
            onChange={(_, value) => setTab(value)}
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
    </ThemeProvider>
  );
}

export default App;
