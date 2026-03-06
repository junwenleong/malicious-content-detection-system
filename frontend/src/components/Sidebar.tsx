import { Box, Stack, Tooltip, Typography } from "@mui/material";
import SearchIcon from "@mui/icons-material/ManageSearch";
import BatchIcon from "@mui/icons-material/TableRows";
import type { NavItem } from "../App";

interface SidebarProps {
  activeNav: NavItem;
  onNavChange: (nav: NavItem) => void;
  healthStatus: "unknown" | "ok" | "error";
}

const NAV_ITEMS: {
  id: NavItem;
  label: string;
  icon: React.ReactNode;
  description: string;
}[] = [
  {
    id: "analyze",
    label: "Analyze",
    icon: <SearchIcon fontSize="small" />,
    description: "Single text analysis",
  },
  {
    id: "batch",
    label: "Batch",
    icon: <BatchIcon fontSize="small" />,
    description: "CSV bulk processing",
  },
];

const STATUS_COLOR: Record<string, string> = {
  ok: "#10b981",
  error: "#ef4444",
  unknown: "#94a3b8",
};

export function Sidebar({
  activeNav,
  onNavChange,
  healthStatus,
}: SidebarProps) {
  return (
    <Box
      component="nav"
      aria-label="Main navigation"
      sx={{
        width: 200,
        flexShrink: 0,
        borderRight: "1px solid",
        borderColor: "divider",
        bgcolor: "background.default",
        display: { xs: "none", sm: "flex" },
        flexDirection: "column",
        py: 2,
        px: 1.5,
        gap: 0.5,
      }}
    >
      {/* Nav section label */}
      <Typography
        variant="subtitle2"
        color="text.secondary"
        sx={{ px: 1, mb: 0.5 }}
      >
        Workspace
      </Typography>

      {NAV_ITEMS.map((item) => {
        const isActive = activeNav === item.id;
        return (
          <Tooltip key={item.id} title={item.description} placement="right">
            <Box
              component="button"
              onClick={() => onNavChange(item.id)}
              aria-current={isActive ? "page" : undefined}
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 1.5,
                px: 1.5,
                py: 1,
                borderRadius: "6px",
                border: "none",
                cursor: "pointer",
                width: "100%",
                textAlign: "left",
                transition: "all 150ms ease",
                bgcolor: isActive ? "primary.main" : "transparent",
                color: isActive ? "#fff" : "text.secondary",
                "&:hover": {
                  bgcolor: isActive ? "primary.main" : "action.hover",
                  color: isActive ? "#fff" : "text.primary",
                },
              }}
            >
              {item.icon}
              <Typography
                variant="body2"
                fontWeight={isActive ? 600 : 500}
                color="inherit"
                sx={{ fontSize: "0.875rem" }}
              >
                {item.label}
              </Typography>
            </Box>
          </Tooltip>
        );
      })}

      {/* Spacer */}
      <Box sx={{ flex: 1 }} />

      {/* API status indicator */}
      <Stack
        direction="row"
        alignItems="center"
        spacing={1}
        sx={{ px: 1.5, py: 1 }}
      >
        <Box
          sx={{
            width: 7,
            height: 7,
            borderRadius: "50%",
            bgcolor: STATUS_COLOR[healthStatus],
            flexShrink: 0,
          }}
        />
        <Typography variant="caption" color="text.secondary" noWrap>
          {healthStatus === "ok"
            ? "API connected"
            : healthStatus === "error"
              ? "API offline"
              : "Checking..."}
        </Typography>
      </Stack>
    </Box>
  );
}
