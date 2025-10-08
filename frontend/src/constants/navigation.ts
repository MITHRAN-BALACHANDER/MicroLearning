import {
  BarChart3,
  LayoutDashboard,
  Users2,
  Video,
  FolderTree,
  type LucideIcon,
} from "lucide-react"

export interface NavItem {
  title: string
  url: string
  icon?: LucideIcon
  isActive?: boolean
  items?: {
    title: string
    url: string
  }[]
}

export interface NavDocumentItem {
  name: string
  url: string
  icon: LucideIcon
}

export const NAV_MAIN: NavItem[] = [
  {
    title: "Dashboard",
    url: "/",
    icon: LayoutDashboard,
  },
  {
    title: "Analytics",
    url: "/analytics",
    icon: BarChart3,
  },
  {
    title: "Users",
    url: "/users",
    icon: Users2,
  },
  {
    title: "Categories",
    url: "/categories",
    icon: FolderTree,
  },
  {
    title: "Videos",
    url: "/videos",
    icon: Video,
  },
]

export const NAV_PROJECTS: NavItem[] = []

export const NAV_SECONDARY: NavItem[] = []

export const NAV_DOCUMENTS: NavDocumentItem[] = []

export const APP_CONFIG = {
  name: "MicroLearning Admin",
  description: "Learning Management Platform",
  version: "2.0.0",
}

export const USER_DATA = {
  name: "Admin User",
  email: "admin@microlearning.com",
  avatar: "/avatars/admin.jpg",
  role: "Administrator",
  initials: "AU",
}
