import { useEffect, useMemo, useState } from "react";
import { Box, CssBaseline, ThemeProvider, useMediaQuery } from "@mui/material";
import { Header } from "./components/Header";
import { Sidebar } from "./components/Sidebar";
import { ConnectionPanel } from "./components/ConnectionPanel";
import { AnalyzeTab } from "./components/AnalyzeTab";
import { BatchTab } from "./components/BatchTab";
import { buildTheme } from "./theme";

const defaultApiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const defaultApiKey = import.meta.env.VITE_DEFAULT_API_KEY ?? "";

export type NavItem = "analyze" | "batch";

function App() {
  const prefersDarkMode = useMediaQuery("(prefers-color-scheme: dark)");

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

  const [activeNav, setActiveNav] = useState<NavItem>("analyze");
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
    if (apiKey.trim()) baseHeaders["x-api-key"] = apiKey.trim();
    return baseHeaders;
  }, [apiKey]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {/* Full-height app shell */}
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          minHeight: "100vh",
          bgcolor: "background.default",
        }}
      >
        <Header mode={mode} onToggleMode={toggleMode} />

        <Box sx={{ display: "flex", flex: 1, overflow: "hidden" }}>
          {/* Left sidebar */}
          <Sidebar
            activeNav={activeNav}
            onNavChange={setActiveNav}
            healthStatus={healthStatus}
          />

          {/* Main workspace */}
          <Box
            component="main"
            sx={{
              flex: 1,
              overflow: "auto",
              p: { xs: 2, md: 3 },
              display: "flex",
              flexDirection: "column",
              gap: 3,
            }}
          >
            <ConnectionPanel
              apiUrl={apiUrl}
              setApiUrl={setApiUrl}
              apiKey={apiKey}
              setApiKey={setApiKey}
              healthStatus={healthStatus}
              healthMessage={healthMessage}
            />

            {activeNav === "analyze" && (
              <AnalyzeTab apiUrl={apiUrl} headers={headers} />
            )}
            {activeNav === "batch" && (
              <BatchTab apiUrl={apiUrl} apiKey={apiKey} />
            )}
          </Box>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App;
