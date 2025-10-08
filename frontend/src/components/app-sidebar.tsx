import * as React from "react"
import { GraduationCap } from "lucide-react"

import { NavMain } from "@/components/nav-main"
import { NavUser } from "@/components/nav-user"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import {
  APP_CONFIG,
  NAV_MAIN,
  USER_DATA,
} from "@/constants/navigation"
import { useModal } from "@/contexts/ModalContext"

const data = {
  user: USER_DATA,
  navMain: NAV_MAIN,
}

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const { openVideoModal, openCategoryModal, openUserModal } = useModal()

  const handleQuickCreate = (type: 'video' | 'category' | 'user') => {
    switch (type) {
      case 'video':
        openVideoModal()
        break
      case 'category':
        openCategoryModal()
        break
      case 'user':
        openUserModal()
        break
    }
  }

  return (
    <Sidebar collapsible="offcanvas" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              asChild
              className="data-[slot=sidebar-menu-button]:!p-1.5"
            >
              <a href="#">
                <GraduationCap className="!size-5" />
                <span className="text-base font-semibold">{APP_CONFIG.name}</span>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} onQuickCreate={handleQuickCreate} />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={data.user} />
      </SidebarFooter>
    </Sidebar>
  )
}
