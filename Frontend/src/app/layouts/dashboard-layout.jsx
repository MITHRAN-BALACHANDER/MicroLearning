import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import {
  Bell,
  ChevronDown,
  Menu,
  MoonStar,
  Search,
  SunMedium,
  UserRound,
} from "lucide-react";

import { NAV_LINKS } from "@/constants/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

const BRANDS = {
  name: "MicroLearning",
  suffix: "Ops",
};

const ADMIN_USER = {
  initials: "JD",
  role: "Administrator",
  // backend: replace with authenticated user details from session/token response
};

export function DashboardLayout({ children }) {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDark);
  }, [isDark]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="flex min-h-screen">
        <Sidebar />

        <div className="flex flex-1 flex-col">
          <TopBar isDark={isDark} setIsDark={setIsDark} />

          <main className="flex-1 overflow-y-auto bg-muted/40 px-6 pb-10 pt-24">
            <div className="mx-auto max-w-7xl space-y-8">{children}</div>
          </main>
        </div>
      </div>
    </div>
  );
}

function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 border-r bg-card/80 backdrop-blur lg:flex lg:flex-col">
      <div className="flex h-16 items-center gap-2 px-6">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground font-semibold">
          {BRANDS.name.slice(0, 1)}
        </div>
        <div className="leading-tight">
          <p className="text-sm font-semibold tracking-tight">{BRANDS.name}</p>
          <p className="text-xs text-muted-foreground uppercase">
            {BRANDS.suffix}
          </p>
        </div>
      </div>
      <Separator />
      <ScrollArea className="flex-1">
        <nav className="space-y-2 px-4 py-6">
          {NAV_LINKS.map((link) => (
            <NavLink
              key={link.path}
              to={link.path}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition hover:bg-accent hover:text-accent-foreground",
                  isActive && "bg-primary text-primary-foreground shadow-sm"
                )
              }
            >
              <link.icon className="h-4 w-4" />
              <span>{link.label}</span>
            </NavLink>
          ))}
        </nav>
      </ScrollArea>
      <Separator />
      <div className="flex items-center gap-3 px-6 py-5 text-sm">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-secondary text-secondary-foreground font-semibold">
          {ADMIN_USER.initials}
        </div>
        <div className="flex-1">
          <p className="font-medium">{ADMIN_USER.initials}</p>
          <p className="text-xs text-muted-foreground">{ADMIN_USER.role}</p>
        </div>
        <Button variant="ghost" size="icon">
          <ChevronDown className="h-4 w-4" />
        </Button>
      </div>
    </aside>
  );
}

function TopBar({ isDark, setIsDark }) {
  return (
    <header className="fixed inset-x-0 top-0 z-40 flex h-16 items-center border-b bg-card/90 px-4 shadow-sm backdrop-blur lg:pl-[17rem]">
      <div className="flex w-full items-center gap-3">
        <div className="flex items-center lg:hidden">
          <MobileNav />
        </div>
        <div className="hidden items-center gap-2 sm:flex">
          <Search className="h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search resources, creators or tags"
            className="h-9 w-64 bg-transparent"
            // backend: wire this search input to a query endpoint to filter content server-side
          />
        </div>

        <div className="ml-auto flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsDark((prev) => !prev)}
          >
            {isDark ? (
              <SunMedium className="h-4 w-4" />
            ) : (
              <MoonStar className="h-4 w-4" />
            )}
            <span className="sr-only">Toggle theme</span>
          </Button>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <Bell className="h-4 w-4" />
                <span className="sr-only">Notifications</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-64" align="end">
              <DropdownMenuLabel>Notifications</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem disabled>
                No new alerts
                {/* backend: replace list with real-time notifications fetched from /notifications */}
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuCheckboxItem checked>
                Email updates
                {/* backend: toggle user notification preferences via PATCH /users/:id/preferences */}
              </DropdownMenuCheckboxItem>
              <DropdownMenuCheckboxItem>Slack sync</DropdownMenuCheckboxItem>
              <DropdownMenuSeparator />
              <DropdownMenuRadioGroup value="daily">
                <DropdownMenuRadioItem value="instant">
                  Instant
                </DropdownMenuRadioItem>
                <DropdownMenuRadioItem value="daily">
                  Daily digest
                </DropdownMenuRadioItem>
                <DropdownMenuRadioItem value="weekly">
                  Weekly summary
                </DropdownMenuRadioItem>
              </DropdownMenuRadioGroup>
            </DropdownMenuContent>
          </DropdownMenu>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="gap-2 px-3">
                <UserRound className="h-4 w-4" />
                <span className="hidden text-sm font-semibold sm:inline">
                  Admin
                </span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end">
              <DropdownMenuLabel>Signed in as Admin</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem>Profile</DropdownMenuItem>
              <DropdownMenuItem>Team settings</DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-destructive">
                Sign out
                {/* backend: invoke logout endpoint and clear auth tokens */}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}

function MobileNav() {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon">
          <Menu className="h-5 w-5" />
          <span className="sr-only">Toggle navigation</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-full max-w-xs p-0">
        <SheetHeader className="flex flex-row items-center justify-between px-4 pt-4">
          <SheetTitle className="text-left">
            <span className="font-semibold">{BRANDS.name}</span>
            <span className="ml-2 rounded-full bg-primary/10 px-2 py-0.5 text-xs uppercase tracking-wide text-primary">
              {BRANDS.suffix}
            </span>
          </SheetTitle>
        </SheetHeader>
        <ScrollArea className="h-full px-4 pb-6">
          <nav className="mt-6 space-y-1">
            {NAV_LINKS.map((link) => (
              <NavLink
                key={link.path}
                to={link.path}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition hover:bg-accent hover:text-accent-foreground",
                    isActive && "bg-primary text-primary-foreground"
                  )
                }
              >
                <link.icon className="h-4 w-4" />
                {link.label}
              </NavLink>
            ))}
          </nav>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
