import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from "react-router-dom"

import { AppSidebar } from "@/components/app-sidebar"
import { AppBreadcrumb } from "@/components/app-breadcrumb"
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { Toaster } from "@/components/ui/sonner"
import { ModalProvider } from "@/contexts/ModalContext"

// Import page components
import Dashboard from "./pages/Dashboard"
import Users from "./pages/Users"
import Categories from "./pages/Categories"
import Videos from "./pages/Videos"
import Analytics from "./pages/Analytics"
import Profile from "./pages/Profile"
import Login from "./pages/Login"

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem("token")
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

function AppLayout() {
  const location = useLocation()
  const isLoginPage = location.pathname === "/login"

  if (isLoginPage) {
    return (
      <>
        <Routes>
          <Route path="/login" element={<Login />} />
        </Routes>
        <Toaster />
      </>
    )
  }

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 transition-[width,height] ease-linear group-has-[[data-collapsible=icon]]/sidebar-wrapper:h-12">
          <div className="flex items-center gap-2 px-4">
            <SidebarTrigger className="-ml-1" />
            <Separator orientation="vertical" className="mr-2 h-4" />
            <AppBreadcrumb />
          </div>
        </header>
        <div className="flex flex-1 flex-col gap-4 p-4 pt-0">
          <Routes>
            <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
            <Route path="/users" element={<ProtectedRoute><Users /></ProtectedRoute>} />
            <Route path="/categories" element={<ProtectedRoute><Categories /></ProtectedRoute>} />
            <Route path="/videos" element={<ProtectedRoute><Videos /></ProtectedRoute>} />
            <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
          </Routes>
        </div>
      </SidebarInset>
      <Toaster />
    </SidebarProvider>
  )
}

function App() {
  return (
    <Router>
      <ModalProvider>
        <AppLayout />
      </ModalProvider>
    </Router>
  )
}

export default App
