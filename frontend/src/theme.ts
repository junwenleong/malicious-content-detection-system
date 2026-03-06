import { createTheme, type PaletteMode } from "@mui/material";

export function buildTheme(mode: PaletteMode) {
  const isDark = mode === "dark";

  return createTheme({
    palette: {
      mode,
      primary: {
        main: isDark ? "#818cf8" : "#6366f1", // indigo-400 / indigo-500
        light: isDark ? "#a5b4fc" : "#818cf8",
        dark: isDark ? "#6366f1" : "#4f46e5",
        contrastText: "#ffffff",
      },
      error: {
        main: isDark ? "#f87171" : "#ef4444",
      },
      warning: {
        main: isDark ? "#fbbf24" : "#f59e0b",
      },
      success: {
        main: isDark ? "#34d399" : "#10b981",
      },
      background: {
        default: isDark ? "#0b0f1a" : "#f1f5f9", // deep navy / slate-100
        paper: isDark ? "#131929" : "#ffffff",
      },
      text: {
        primary: isDark ? "#e2e8f0" : "#0f172a",
        secondary: isDark ? "#94a3b8" : "#64748b",
      },
      divider: isDark ? "#1e2d45" : "#e2e8f0",
    },
    typography: {
      fontFamily: [
        "Inter",
        "-apple-system",
        "BlinkMacSystemFont",
        '"Segoe UI"',
        "sans-serif",
      ].join(","),
      h4: { fontWeight: 700, letterSpacing: "-0.025em" },
      h5: { fontWeight: 700, letterSpacing: "-0.02em" },
      h6: { fontWeight: 600, letterSpacing: "-0.01em" },
      subtitle1: { fontWeight: 600 },
      subtitle2: {
        fontWeight: 600,
        letterSpacing: "0.02em",
        fontSize: "0.7rem",
        textTransform: "uppercase" as const,
      },
      body2: { color: isDark ? "#94a3b8" : "#64748b" },
    },
    shape: {
      borderRadius: 8,
    },
    components: {
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: "none",
            border: `1px solid ${isDark ? "#1e2d45" : "#e2e8f0"}`,
            boxShadow: "none",
          },
          outlined: {
            border: `1px solid ${isDark ? "#1e2d45" : "#e2e8f0"}`,
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            backgroundImage: "none",
            backgroundColor: isDark ? "#0b0f1a" : "#ffffff",
            borderBottom: `1px solid ${isDark ? "#1e2d45" : "#e2e8f0"}`,
            boxShadow: "none",
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            fontWeight: 600,
            fontSize: "0.72rem",
            height: 22,
            borderRadius: 6,
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: "none",
            fontWeight: 600,
            letterSpacing: "-0.01em",
            boxShadow: "none",
            "&:hover": { boxShadow: "none" },
          },
          contained: {
            background: isDark
              ? "linear-gradient(135deg, #6366f1 0%, #818cf8 100%)"
              : "linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)",
          },
        },
      },
      MuiTab: {
        styleOverrides: {
          root: {
            textTransform: "none",
            fontWeight: 600,
            fontSize: "0.875rem",
            letterSpacing: "-0.01em",
            minHeight: 44,
          },
        },
      },
      MuiTabs: {
        styleOverrides: {
          root: {
            borderBottom: `1px solid ${isDark ? "#1e2d45" : "#e2e8f0"}`,
            minHeight: 44,
          },
        },
      },
      MuiTextField: {
        styleOverrides: {
          root: {
            "& .MuiOutlinedInput-root": {
              "& fieldset": {
                borderColor: isDark ? "#1e2d45" : "#e2e8f0",
              },
              "&:hover fieldset": {
                borderColor: isDark ? "#6366f1" : "#6366f1",
              },
            },
          },
        },
      },
      MuiLinearProgress: {
        styleOverrides: {
          root: {
            borderRadius: 6,
            height: 6,
            backgroundColor: isDark ? "#1e2d45" : "#e2e8f0",
          },
        },
      },
      MuiAlert: {
        styleOverrides: {
          root: {
            border: "none",
            borderRadius: 8,
          },
        },
      },
      MuiDivider: {
        styleOverrides: {
          root: {
            borderColor: isDark ? "#1e2d45" : "#e2e8f0",
          },
        },
      },
    },
  });
}
