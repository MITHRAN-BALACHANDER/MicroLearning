import { Plus, Video, FolderTree, Users, type LucideIcon } from "lucide-react"
import { useLocation } from "react-router-dom"

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

export function NavMain({
  items,
  onQuickCreate,
}: {
  items: {
    title: string
    url: string
    icon?: LucideIcon
  }[]
  onQuickCreate?: (type: 'video' | 'category' | 'user') => void
}) {
  const location = useLocation()

  const handleQuickCreate = (type: 'video' | 'category' | 'user') => {
    if (onQuickCreate) {
      onQuickCreate(type)
    }
  }

  return (
    <SidebarGroup>
      <SidebarGroupContent className="flex flex-col gap-2">
        <SidebarMenu>
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton
                  tooltip="Quick Create"
                  className="bg-primary text-primary-foreground hover:bg-primary/90 hover:text-primary-foreground data-[state=open]:bg-primary/90 data-[state=open]:text-primary-foreground"
                >
                  <Plus />
                  <span>Quick Create</span>
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent side="right" align="start" className="w-48">
                <DropdownMenuItem onClick={() => handleQuickCreate('video')}>
                  <Video className="mr-2 h-4 w-4" />
                  New Video
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleQuickCreate('category')}>
                  <FolderTree className="mr-2 h-4 w-4" />
                  New Category
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleQuickCreate('user')}>
                  <Users className="mr-2 h-4 w-4" />
                  New User
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        </SidebarMenu>
        <SidebarMenu>
          {items.map((item) => {
            const isActive = location.pathname === item.url || 
                           (item.url !== '/' && location.pathname.startsWith(item.url))
            
            return (
              <SidebarMenuItem key={item.title}>
                <SidebarMenuButton 
                  tooltip={item.title} 
                  asChild
                  isActive={isActive}
                >
                  <a href={item.url}>
                    {item.icon && <item.icon />}
                    <span>{item.title}</span>
                  </a>
                </SidebarMenuButton>
              </SidebarMenuItem>
            )
          })}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  )
}
