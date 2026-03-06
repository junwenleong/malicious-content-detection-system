import { createTheme, type PaletteMode } from "@mui/material";

export function buildTheme(mode: PaletteMode) {
  const isDark = mode === "dark";

  return createTheme({
    palette: {
      mode,
      primary: {
        main: isDark ? "#60a5fa" : "#2563eb", // blue-400 / blue-600
        light: isDark ? "#93c5fd" : "#3b82f6",
        dark: isDark ? "#3b82f6" : "#1d4ed8",
      },
      error: {
        main: isDark ? "#f87171" : "#dc2626", // red-400 / red-600
      },
      warning: {
        main: isDark ? "#fbbf24" : "#d97706", // amber-400 / amber-600
      },
      success: {
        main: isDark ? "#34d399" : "#16a34a", // emerald-400 / green-600
      },
      background: {
        default: isDark ? "#0f172a" : "#f8fafc", // slate-900 / slate-50
        paper: isDark ? "#1e293b" : "#ffffff", // slate-800 / white
      },
      text: {
        primary: isDark ? "#f1f5f9" : "#0f172a", // slate-100 / slate-900
        secondary: isDark ? "#94a3b8" : "#475569", // slate-400 / slate-600
      },
      divider: isDark ? "#334155" : "#e2e8f0", // slate-700 / slate-200
    },
    typography: {
      fontFamily: [
        "Inter",
        "-apple-system",
        "BlinkMacSystemFont",
        '"Segoe UI"',
        "sans-serif",
      ].join(","),
      h4: { fontWeight: 700, letterSpacing: "-0.02em" },
      h6: { fontWeight: 600 },
    },
    shape: {
      borderRadius: 10,
    },
    components: {
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: "none", // disable MUI dark mode overlay tint
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            backgroundImage: "none",
            backgroundColor: isDark ? "#0f172a" : "#ffffff",
            borderBottom: `1px solid ${isDark ? "#1e293b" : "#e2e8f0"}`,
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            fontWeight: 600,
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: "none",
            fontWeight: 600,
          },
        },
      },
      MuiLinearProgress: {
        styleOverrides: {
          root: {
            borderRadius: 6,
          },
        },
      },
    },
  });
}
