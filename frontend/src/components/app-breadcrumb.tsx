import { useLocation } from "react-router-dom"
import { 
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"

interface BreadcrumbConfig {
  [key: string]: {
    label: string
    parent?: string
  }
}

const breadcrumbConfig: BreadcrumbConfig = {
  "/": { label: "Dashboard" },
  "/analytics": { label: "Analytics" },
  "/content-management": { label: "Content Library" },
  "/upload-content": { label: "Upload Content", parent: "/content-management" },
  "/users": { label: "Users" },
  "/feedback": { label: "Feedback" },
  "/logs": { label: "System Logs" },
  "/settings": { label: "Settings" },
  "/learning-paths": { label: "Learning Paths" },
  "/assessments": { label: "Assessments" },
  "/goals": { label: "Goals & Targets" },
}

export function AppBreadcrumb() {
  const location = useLocation()
  const currentPath = location.pathname

  const generateBreadcrumbs = (path: string) => {
    const breadcrumbs = []
    const config = breadcrumbConfig[path]
    
    if (!config) return []

    // Add parent breadcrumb if exists
    if (config.parent && breadcrumbConfig[config.parent]) {
      breadcrumbs.push({
        label: breadcrumbConfig[config.parent].label,
        href: config.parent,
      })
    }

    // Add current page
    breadcrumbs.push({
      label: config.label,
      href: path,
      isCurrentPage: true,
    })

    return breadcrumbs
  }

  const breadcrumbs = generateBreadcrumbs(currentPath)

  if (breadcrumbs.length === 0) return null

  return (
    <Breadcrumb>
      <BreadcrumbList>
        <BreadcrumbItem className="hidden md:block">
          <BreadcrumbLink href="/">
            MicroLearning Platform
          </BreadcrumbLink>
        </BreadcrumbItem>
        {breadcrumbs.map((breadcrumb) => (
          <div key={breadcrumb.href} className="flex items-center">
            <BreadcrumbSeparator className="hidden md:block" />
            <BreadcrumbItem>
              {breadcrumb.isCurrentPage ? (
                <BreadcrumbPage>{breadcrumb.label}</BreadcrumbPage>
              ) : (
                <BreadcrumbLink href={breadcrumb.href}>
                  {breadcrumb.label}
                </BreadcrumbLink>
              )}
            </BreadcrumbItem>
          </div>
        ))}
      </BreadcrumbList>
    </Breadcrumb>
  )
}
