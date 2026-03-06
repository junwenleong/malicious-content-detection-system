import {
  AppBar,
  Box,
  Chip,
  IconButton,
  Stack,
  Toolbar,
  Tooltip,
  Typography,
} from "@mui/material";
import DarkModeIcon from "@mui/icons-material/DarkMode";
import LightModeIcon from "@mui/icons-material/LightMode";
import ShieldIcon from "@mui/icons-material/Shield";

interface HeaderProps {
  mode: "light" | "dark";
  onToggleMode: () => void;
}

export function Header({ mode, onToggleMode }: HeaderProps) {
  return (
    <AppBar position="static" elevation={0}>
      <Toolbar sx={{ px: { xs: 2, md: 3 }, minHeight: "56px !important" }}>
        {/* Brand */}
        <Stack
          direction="row"
          alignItems="center"
          spacing={1.5}
          sx={{ flex: 1 }}
        >
          <Box
            sx={{
              width: 30,
              height: 30,
              borderRadius: "8px",
              background: "linear-gradient(135deg, #4f46e5 0%, #818cf8 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <ShieldIcon sx={{ fontSize: 16, color: "#fff" }} />
          </Box>
          <Typography
            variant="subtitle1"
            fontWeight={700}
            letterSpacing="-0.02em"
            color="text.primary"
            noWrap
          >
            Content Safety
          </Typography>
          <Chip
            label="v1.0"
            size="small"
            sx={{
              height: 18,
              fontSize: "0.65rem",
              fontWeight: 700,
              bgcolor: "primary.main",
              color: "#fff",
              borderRadius: "4px",
            }}
          />
        </Stack>

        {/* Right controls */}
        <Tooltip title={`Switch to ${mode === "dark" ? "light" : "dark"} mode`}>
          <IconButton
            onClick={onToggleMode}
            size="small"
            aria-label={`Switch to ${mode === "dark" ? "light" : "dark"} mode`}
            sx={{
              color: "text.secondary",
              "&:hover": { color: "text.primary" },
            }}
          >
            {mode === "dark" ? (
              <LightModeIcon fontSize="small" />
            ) : (
              <DarkModeIcon fontSize="small" />
            )}
          </IconButton>
        </Tooltip>
      </Toolbar>
    </AppBar>
  );
}
