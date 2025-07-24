import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import {
  Users,
  Clock,
  ArrowUp,
  ArrowDown,
  Target,
  BookOpen,
  Calendar,
} from "lucide-react";
import { useSelector } from "react-redux";
import Button from "../components/Button";
import {exportToExcel} from "../utils/excelDownload";
export default function Analytics() {
  const {
    chartData,
    testStats,
    topPerformers,
    pieData,
    weeklyData,
  } = useSelector((state) => state.analytics);

  const kpiCards = [
    {
      title: "Total Tests Taken",
      value: "12,847",
      change: "+18.2%",
      changeType: "positive",
      icon: BookOpen,
      description: "This month",
    },
    {
      title: "Active Learners",
      value: "2,341",
      change: "+12.5%",
      changeType: "positive",
      icon: Users,
      description: "Last 30 days",
    },
    {
      title: "Avg. Study Time",
      value: "4.2h",
      change: "-2.1%",
      changeType: "negative",
      icon: Clock,
      description: "Per session",
    },
    {
      title: "Completion Rate",
      value: "87.3%",
      change: "+5.8%",
      changeType: "positive",
      icon: Target,
      description: "Overall",
    },
  ];
  const handleDownload = () => {
   exportToExcel()
  };

  return (
    <div className="min-h-screen mt-10 bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Learning Analytics Dashboard
          </h1>
          <div className="flex items-center justify-between">
            <p className="text-gray-600">
              Real-time performance insights and metrics
            </p>
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <Calendar className="w-4 h-4" />
              <span>Last updated: 2 minutes ago</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 mt-19 gap-4 mb-6">
          {kpiCards.map((kpi, i) => (
            <div
              key={i}
              className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="p-2 bg-blue-50 rounded-lg">
                  <kpi.icon className="w-5 h-5 text-blue-600" />
                </div>
                <div
                  className={`flex items-center gap-1 text-sm font-medium ${
                    kpi.changeType === "positive"
                      ? "text-green-600"
                      : "text-red-600"
                  }`}
                >
                  {kpi.changeType === "positive" ? (
                    <ArrowUp className="w-4 h-4" />
                  ) : (
                    <ArrowDown className="w-4 h-4" />
                  )}
                  {kpi.change}
                </div>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-1">
                {kpi.value}
              </h3>
              <p className="text-sm text-gray-600 mb-1">{kpi.title}</p>
              <p className="text-xs text-gray-500">{kpi.description}</p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
          <div className="lg:col-span-2 bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Test Participation Trends
                </h3>
                <p className="text-sm text-gray-600">
                  Daily test completions over the last 7 days
                </p>
              </div>
              <div className="flex items-center gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                  <span className="text-gray-600">Current Period</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-gray-300 rounded-full"></div>
                  <span className="text-gray-600">Previous Period</span>
                </div>
              </div>
            </div>

            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 12, fill: "#6B7280" }}
                  tickLine={false}
                  axisLine={{ stroke: "#E5E7EB" }}
                />
                <YAxis
                  tick={{ fontSize: 12, fill: "#6B7280" }}
                  tickLine={false}
                  axisLine={{ stroke: "#E5E7EB" }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "white",
                    border: "1px solid #E5E7EB",
                    borderRadius: "8px",
                    boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#3B82F6"
                  strokeWidth={2}
                  dot={{ fill: "#3B82F6", strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, fill: "#3B82F6" }}
                />
                <Line
                  type="monotone"
                  dataKey="previous"
                  stroke="#D1D5DB"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={{ fill: "#D1D5DB", strokeWidth: 2, r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Pie Chart */}
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Course Progress
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Overall completion status
            </p>

            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value) => [`${value}%`, "Percentage"]}
                  contentStyle={{
                    backgroundColor: "white",
                    border: "1px solid #E5E7EB",
                    borderRadius: "8px",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>

            <div className="space-y-2 mt-4">
              {pieData.map((item, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between text-sm"
                >
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: item.color }}
                    ></div>
                    <span className="text-gray-700">{item.name}</span>
                  </div>
                  <span className="font-medium text-gray-900">
                    {item.value}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Score Distribution
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Performance breakdown by grade ranges
            </p>

            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={testStats}>
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 11, fill: "#6B7280" }}
                  tickLine={false}
                  axisLine={{ stroke: "#E5E7EB" }}
                  interval={0}
                />
                <YAxis
                  tick={{ fontSize: 12, fill: "#6B7280" }}
                  tickLine={false}
                  axisLine={{ stroke: "#E5E7EB" }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "white",
                    border: "1px solid #E5E7EB",
                    borderRadius: "8px",
                  }}
                />
                <Bar dataKey="value" fill="#3B82F6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Top Performers
                </h3>
                <p className="text-sm text-gray-600">
                  Highest scoring students this month
                </p>
              </div>
              <Button
                onClick={() => handleDownload()}
                text="Download report"
                color="green"
               
              />
            </div>

            <div className="space-y-3">
              {topPerformers.map((user, i) => (
                <div
                  key={i}
                  className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-sm font-semibold text-blue-600">
                        #{i + 1}
                      </span>
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium text-gray-900">{user.name}</h4>
                      <span className="text-lg font-bold text-blue-600">
                        {user.rating}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <div className="flex items-center gap-3">
                        <span>{user.tests} tests</span>
                        <span className="text-green-600 font-medium">
                          {user.improvement}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
