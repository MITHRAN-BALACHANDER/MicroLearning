import {
  BarChart3,
  FileSpreadsheet,
  FolderUp,
  LayoutDashboard,
  LineChart,
  MessageSquareText,
  Settings,
  Users2,
} from "lucide-react";

export const NAV_LINKS = [
  {
    label: "Dashboard",
    icon: LayoutDashboard,
    path: "/",
  },
  {
    label: "Content Library",
    icon: FileSpreadsheet,
    path: "/content-management",
  },
  {
    label: "Upload",
    icon: FolderUp,
    path: "/upload-content",
  },
  {
    label: "Users",
    icon: Users2,
    path: "/users",
  },
  {
    label: "Analytics",
    icon: LineChart,
    path: "/analytics",
  },
  {
    label: "Feedback",
    icon: MessageSquareText,
    path: "/feedback",
  },
  {
    label: "Logs",
    icon: BarChart3,
    path: "/logs",
  },
  {
    label: "Settings",
    icon: Settings,
    path: "/settings",
  },
];
