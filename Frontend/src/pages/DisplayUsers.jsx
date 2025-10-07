import { useMemo, useState } from "react";
import { DownloadCloud, Search, UserPlus, UsersIcon } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const MOCK_USERS = [
  {
    name: "Sahana",
    role: "Sales Representative",
    department: "Finance",
    empId: 1,
  },
  { name: "Kavin", role: "Marketing Head", department: "Growth", empId: 2 },
  { name: "Nandha", role: "HR Partner", department: "People Ops", empId: 3 },
  // backend: replace mock with GET /users?limit=...
];

const METRICS = [
  {
    label: "Total users",
    value: 1234,
    delta: "+4% vs last month",
  },
  {
    label: "Active this week",
    value: 123,
    delta: "-3% vs last week",
  },
  {
    label: "New invites",
    value: 12,
    delta: "+6% vs target",
  },
];

const PAGE_SIZE = 5;

export default function DisplayUsers() {
  const [users, setUsers] = useState(MOCK_USERS);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [form, setForm] = useState({
    name: "",
    role: "",
    department: "",
    empId: "",
  });

  const filtered = useMemo(() => {
    if (!search) return users;
    const lower = search.toLowerCase();
    return users.filter((user) =>
      [user.name, user.role, user.department].some((field) =>
        field.toLowerCase().includes(lower)
      )
    );
  }, [search, users]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const handleSubmit = () => {
    if (!form.name || !form.role || !form.department || !form.empId) return;
    setUsers((prev) => [
      ...prev,
      {
        name: form.name,
        role: form.role,
        department: form.department,
        empId: Number(form.empId),
      },
    ]);
    setForm({ name: "", role: "", department: "", empId: "" });
    // backend: POST /users with payload { name, role, department, employeeId }
  };

  return (
    <section className="space-y-8">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            People directory
          </h1>
          <p className="text-sm text-muted-foreground">
            View active learners, invite teammates, and manage access.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button variant="outline" className="gap-2">
            <DownloadCloud className="h-4 w-4" />
            Export report
            {/* backend: call GET /users/export to download CSV */}
          </Button>
          <Dialog>
            <DialogTrigger asChild>
              <Button className="gap-2">
                <UserPlus className="h-4 w-4" />
                Add user
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Invite a teammate</DialogTitle>
                <DialogDescription>
                  Capture the essentials and well send them an activation email.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-3 py-2">
                <div className="space-y-1">
                  <Label htmlFor="name">Full name</Label>
                  <Input
                    id="name"
                    value={form.name}
                    onChange={(event) =>
                      setForm((prev) => ({ ...prev, name: event.target.value }))
                    }
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="role">Role</Label>
                  <Input
                    id="role"
                    value={form.role}
                    onChange={(event) =>
                      setForm((prev) => ({ ...prev, role: event.target.value }))
                    }
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="department">Department</Label>
                  <Input
                    id="department"
                    value={form.department}
                    onChange={(event) =>
                      setForm((prev) => ({
                        ...prev,
                        department: event.target.value,
                      }))
                    }
                    // backend: replace with dropdown fed by GET /departments
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="employeeId">Employee ID</Label>
                  <Input
                    id="employeeId"
                    type="number"
                    value={form.empId}
                    onChange={(event) =>
                      setForm((prev) => ({
                        ...prev,
                        empId: event.target.value,
                      }))
                    }
                  />
                </div>
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() =>
                    setForm({ name: "", role: "", department: "", empId: "" })
                  }
                >
                  Reset
                </Button>
                <Button onClick={handleSubmit}>Send invite</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {METRICS.map((metric) => (
          <Card key={metric.label} className="border-border/70">
            <CardHeader className="pb-2">
              <CardDescription>{metric.label}</CardDescription>
              <CardTitle className="text-3xl font-semibold">
                {metric.value}
              </CardTitle>
            </CardHeader>
            <CardFooter className="text-xs text-muted-foreground">
              {metric.delta}
            </CardFooter>
          </Card>
        ))}
      </div>

      <Card className="border-border/70">
        <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            <UsersIcon className="h-4 w-4" />
            <CardTitle className="text-lg">Directory</CardTitle>
          </div>
          <div className="relative w-full max-w-xs">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search people"
              className="pl-9"
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setPage(1);
              }}
            />
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="max-h-[420px]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Employee</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Department</TableHead>
                  <TableHead className="text-right">Employee ID</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginated.length ? (
                  paginated.map((user) => (
                    <TableRow key={`${user.empId}-${user.name}`}>
                      <TableCell className="font-medium">{user.name}</TableCell>
                      <TableCell>{user.role}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="capitalize">
                          {user.department}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">{user.empId}</TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell
                      colSpan={4}
                      className="py-8 text-center text-sm text-muted-foreground"
                    >
                      No matches yet.{" "}
                      {/* backend: show skeleton while /users is loading */}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </ScrollArea>
        </CardContent>
        <Separator />
        <CardFooter className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <span className="text-xs text-muted-foreground">
            Showing {(page - 1) * PAGE_SIZE + 1}–
            {Math.min(page * PAGE_SIZE, filtered.length)} of {filtered.length}{" "}
            people
          </span>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page === 1}
              onClick={() => setPage((prev) => Math.max(1, prev - 1))}
            >
              Previous
            </Button>
            <Badge variant="outline">Page {page}</Badge>
            <Button
              variant="outline"
              size="sm"
              disabled={page === totalPages}
              onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
            >
              Next
            </Button>
          </div>
        </CardFooter>
      </Card>
    </section>
  );
}
