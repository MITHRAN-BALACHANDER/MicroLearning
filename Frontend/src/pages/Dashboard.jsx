import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import {
  Area,
  AreaChart,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  Activity,
  AlertCircle,
  ArrowUpRight,
  BookOpen,
  Download,
  Eye,
  MapPin,
  Play,
  TrendingUp,
  Users,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Separator } from "@/components/ui/separator";
import { exportToExcel } from "@/utils/excelDownload";
import { fetchDashboardData } from "@/store/DashboardSlice";
import { cn } from "@/lib/utils";

const STAT_CONFIG = [
  {
    label: "Active Users",
    icon: Users,
    change: "+12%",
    extract: ({ activeUsers }) => activeUsers?.value ?? 0,
  },
  {
    label: "Engagement",
    icon: Eye,
    change: "+8%",
    extract: ({ engagementStats }) => engagementStats?.[0]?.value ?? 0,
  },
  {
    label: "Avg. Course Score",
    icon: TrendingUp,
    change: "+5%",
    extract: ({ performanceData }) => performanceData?.[3]?.score ?? 0,
  },
  {
    label: "Uploads Pending",
    icon: Play,
    change: "-3%",
    extract: ({ videoStats }) => videoStats?.toBeVerified ?? 0,
  },
];

export default function Dashboard() {
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const {
    activeUsers,
    engagementStats,
    videoStats,
    courseCompletion,
    regionData,
    complaints,
    activityData,
    performanceData,
  } = useSelector((state) => state.dashboard);

  useEffect(() => {
    dispatch(fetchDashboardData());
    // backend: ensure fetchDashboardData triggers GET /analytics/overview with auth headers
  }, [dispatch]);

  const handleDownload = () => {
    exportToExcel();
    // backend: replace util with server-side export by calling GET /reports/employee-tests
  };

  const stats = STAT_CONFIG.map((item) => ({
    ...item,
    value: item.extract({
      activeUsers,
      engagementStats,
      videoStats,
      courseCompletion,
      regionData,
      complaints,
      activityData,
      performanceData,
    }),
  }));

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Operations overview
          </h1>
          <p className="text-sm text-muted-foreground">
            Monitor live engagement, course progress and recent issues across
            the fleet.
          </p>
        </div>
        <Button variant="secondary" className="gap-2" onClick={handleDownload}>
          <Download className="h-4 w-4" />
          Export Summary
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.label} className="relative overflow-hidden">
            <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
              <div>
                <CardDescription>{stat.label}</CardDescription>
                <CardTitle className="text-3xl font-semibold">
                  {formatMetric(stat.value)}
                </CardTitle>
              </div>
              <Badge variant="outline" className="gap-1 text-xs">
                <ArrowUpRight className="h-3 w-3" />
                {stat.change}
              </Badge>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                Updated just now{" "}
                {/* backend: replace with `lastSynced` timestamp returned by overview endpoint */}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="lg:col-span-1">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-base">
                <Activity className="h-4 w-4" /> Active sessions
              </CardTitle>
              <CardDescription>
                User interactions in the last 24 hours
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={activityData}>
                <defs>
                  <linearGradient id="activity" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0f172a" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#0f172a" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="time"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 12 }}
                />
                <YAxis hide />
                <Tooltip cursor={{ strokeDasharray: "4 4" }} />
                <Area
                  type="monotone"
                  dataKey="users"
                  stroke="#0f172a"
                  fill="url(#activity)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <TrendingUp className="h-4 w-4" /> Monthly performance
            </CardTitle>
            <CardDescription>
              Completion score across flagship programs
            </CardDescription>
          </CardHeader>
          <CardContent className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={performanceData}>
                <XAxis
                  dataKey="month"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 12 }}
                />
                <YAxis hide />
                <Tooltip cursor={{ strokeDasharray: "4 4" }} />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="#2563eb"
                  strokeWidth={3}
                  dot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Eye className="h-4 w-4" /> Engagement mix
            </CardTitle>
            <CardDescription>
              How learners interact with your content
            </CardDescription>
          </CardHeader>
          <CardContent className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={engagementStats}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={4}
                >
                  {engagementStats.map((slice, index) => (
                    <Cell key={slice.name} fill={slice.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-primary/5 via-background to-background">
          <CardHeader className="flex flex-row items-center justify-between pb-4">
            <div>
              <CardTitle className="flex items-center gap-2 text-base">
                <Play className="h-4 w-4" /> Video operations
              </CardTitle>
              <CardDescription>Publishing throughput this week</CardDescription>
            </div>
            <Badge variant="secondary">+4 new</Badge>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3">
              <StatBlock label="Uploaded" value={videoStats.uploaded} />
              <StatBlock
                label="Awaiting QA"
                value={videoStats.toBeVerified}
                tone="warning"
              />
            </div>
          </CardContent>
          <CardFooter>
            <Button
              className="w-full"
              onClick={() => navigate("/upload-content")}
            >
              Manage uploads
            </Button>
          </CardFooter>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <MapPin className="h-4 w-4" /> Regional focus
            </CardTitle>
            <CardDescription>
              Adoption by locale and language preference
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            {regionData.map((region) => (
              <div
                key={region.name}
                className="space-y-2 rounded-lg border bg-muted/40 p-3"
              >
                <div className="flex items-center justify-between text-sm font-medium">
                  <span>{region.name}</span>
                  <Badge variant="outline">{region.value}%</Badge>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${region.value}%`,
                      backgroundColor: region.color,
                    }}
                  />
                </div>
                <p className="text-xs text-muted-foreground">
                  {/* backend: replace with locale-specific insight from /analytics/regions */}
                  Engagement steady week over week
                </p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <AlertCircle className="h-4 w-4" /> Escalations
            </CardTitle>
            <CardDescription>
              Most recent feedback items requiring follow-up
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {complaints.slice(0, 4).map((item) => (
              <div
                key={`${item.user}-${item.time}`}
                className="rounded-lg border bg-card/80 p-3"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-medium">{item.user}</p>
                    <p className="text-xs text-muted-foreground">{item.time}</p>
                  </div>
                  <Badge
                    variant={getSeverityVariant(item.severity)}
                    className="capitalize"
                  >
                    {item.severity}
                  </Badge>
                </div>
                <Separator className="my-2" />
                <p className="text-sm text-muted-foreground">{item.issue}</p>
                <Button variant="outline" size="sm" className="mt-3">
                  View thread
                  {/* backend: navigate to /feedback/:ticketId once API provides identifiers */}
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-base">
              <BookOpen className="h-4 w-4" /> Course completion
            </CardTitle>
            <CardDescription>
              Progress across flagship learning paths
            </CardDescription>
          </div>
          <Badge variant="outline">
            {courseCompletion.percentage}% overall
          </Badge>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Region</TableHead>
                <TableHead>Completed</TableHead>
                <TableHead>In progress</TableHead>
                <TableHead className="text-right">Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {regionData.map((region) => (
                <TableRow key={`${region.name}-completion`}>
                  <TableCell className="font-medium">{region.name}</TableCell>
                  <TableCell>
                    {Math.round(
                      (region.value / 100) * courseCompletion.totalCompleted
                    )}
                  </TableCell>
                  <TableCell>
                    {Math.round(
                      (1 - region.value / 100) * courseCompletion.totalCompleted
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <Badge variant="secondary">On track</Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

function formatMetric(value) {
  if (value === undefined || value === null || value === "--") return "--";
  if (typeof value === "number") {
    if (value >= 1000) return `${(value / 1000).toFixed(1)}k`;
    return value.toLocaleString();
  }
  return value;
}

function StatBlock({ label, value, tone = "default" }) {
  const palette = {
    default: "bg-primary/5 text-primary",
    warning: "bg-amber-100/60 text-amber-700",
    success: "bg-emerald-100/60 text-emerald-700",
  };
  return (
    <div className="space-y-1 rounded-lg border bg-card p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-2xl font-semibold tracking-tight">{value}</p>
      <span
        className={cn(
          "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium",
          palette[tone]
        )}
      >
        {tone === "warning" ? "Action needed" : "Healthy"}
      </span>
    </div>
  );
}

function getSeverityVariant(severity) {
  switch (severity) {
    case "high":
      return "destructive";
    case "medium":
      return "secondary";
    default:
      return "outline";
  }
}
