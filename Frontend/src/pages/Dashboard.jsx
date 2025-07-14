import React, { useEffect, useState } from "react";
import { Download, Users, Play, BookOpen, AlertCircle, TrendingUp, Activity, MapPin, Zap, Eye, Award } from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, Area, AreaChart, LineChart, Line
} from "recharts";
import { useNavigate } from "react-router";


const Dashboard = () => {
  const [realTimeData, setRealTimeData] = useState([]);
  const [currentTime, setCurrentTime] = useState(new Date());

  // Mock data for demonstration
  const activeUsers = [
    { name: "Yesterday", users: 120 },
    { name: "Today", users: 150 }
  ];

  const engagementStats = [
    { name: "Videos", value: 45, color: "#FF6B6B" },
    { name: "Tests", value: 30, color: "#4ECDC4" },
    { name: "Discussions", value: 15, color: "#45B7D1" },
    { name: "Downloads", value: 10, color: "#FFA07A" }
  ];

  const videoStats = { uploaded: 234, toBeVerified: 12 };
  const courseCompletion = { totalCompleted: 1847, percentage: 78 };

  const regionData = [
    { name: "Tamil", value: 85, trend: "up", color: "#FF6B6B" },
    { name: "English", value: 72, trend: "down", color: "#4ECDC4" },
    { name: "Kannada", value: 94, trend: "up", color: "#45B7D1" },
    { name: "Hindi", value: 45, trend: "stable", color: "#FFA07A" },
    { name: "Malayalam", value: 38, trend: "up", color: "#98D8C8" },
    { name: "Telugu", value: 56, trend: "down", color: "#F7DC6F" }
  ];

  const complaints = [
    { user: "John Doe", issue: "Video playback issues", time: "2h ago", severity: "high" },
    { user: "Jane Smith", issue: "Login problems", time: "4h ago", severity: "medium" },
    { user: "Mike Johnson", issue: "Course content missing", time: "6h ago", severity: "low" }
  ];

  const activityData = [
    { time: "6AM", users: 23, engagement: 45 },
    { time: "9AM", users: 89, engagement: 78 },
    { time: "12PM", users: 156, engagement: 92 },
    { time: "3PM", users: 134, engagement: 87 },
    { time: "6PM", users: 98, engagement: 65 },
    { time: "9PM", users: 67, engagement: 54 }
  ];

  const performanceData = [
    { month: "Jan", score: 85 },
    { month: "Feb", score: 88 },
    { month: "Mar", score: 92 },
    { month: "Apr", score: 89 },
    { month: "May", score: 94 },
    { month: "Jun", score: 96 }
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
      setRealTimeData(prev => [
        ...prev.slice(-6),
        { time: new Date().toLocaleTimeString(), value: Math.floor(Math.random() * 100) + 50 }
      ]);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleDownload = () => {
    alert('Download functionality would be implemented here');
  };

  const handleUploadNavigation = () => {
    alert('Navigation to upload content would be implemented here');
  };

  const getTrendIcon = (trend) => {
    switch(trend) {
      case 'up': return <TrendingUp className="w-3 h-3 text-green-500" />;
      case 'down': return <TrendingUp className="w-3 h-3 text-red-500 rotate-180" />;
      default: return <div className="w-3 h-3 bg-gray-400 rounded-full" />;
    }
  };
      const nav=useNavigate();


  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 mt-10 via-white to-blue-50 p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Animated Header */}
        <div className="relative">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-200 via-purple-200 to-pink-200 rounded-3xl blur-xl opacity-20 "></div>
          <div className="relative bg-white/80 backdrop-blur-sm rounded-3xl p-8 shadow-2xl">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-4xl font-bold text-black bg-clip-text ">
                  Analytics
                </h1>
                <p className="text-gray-600 mt-2">Real-time insights • {currentTime.toLocaleTimeString()}</p>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white px-4 py-2 rounded-full shadow-lg">
                  <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium">Live</span>
                </div>
             
              </div>
            </div>
          </div>
        </div>

        {/* Interactive Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { icon: Users, label: "Active Users", value: "1,234", change: "+12%", color: "from-blue-500 to-cyan-500" },
            { icon: Eye, label: "Page Views", value: "45.2K", change: "+8%", color: "from-purple-500 to-pink-500" },
            { icon: Award, label: "Completion Rate", value: "78%", change: "+5%", color: "from-green-500 to-emerald-500" },
            { icon: TrendingUp, label: "Engagement", value: "92%", change: "+15%", color: "from-orange-500 to-red-500" }
          ].map((stat, index) => (
            <div key={index} className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r opacity-0 group-hover:opacity-20 transition-opacity duration-300 rounded-2xl blur-xl" style={{background: `linear-gradient(135deg, ${stat.color.split(' ')[1]}, ${stat.color.split(' ')[3]})`}}></div>
              <div className="relative bg-white rounded-2xl p-6 shadow-xl group-hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
                <div className="flex items-center justify-between mb-4">
                  <div className={`p-3 bg-gradient-to-br ${stat.color} text-white rounded-xl shadow-lg`}>
                    <stat.icon className="w-5 h-5" />
                  </div>
                  <span className="text-sm font-medium text-green-600 bg-green-50 px-2 py-1 rounded-full">
                    {stat.change}
                  </span>
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-1">{stat.value}</h3>
                <p className="text-sm text-gray-600">{stat.label}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Main Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Enhanced Activity Chart */}
          <div className="bg-white rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 text-white rounded-lg">
                <Activity className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">Daily Activity</h2>
                <p className="text-sm text-gray-600">User engagement patterns</p>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={activityData}>
                <defs>
                  <linearGradient id="colorActivity" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.1}/>
                  </linearGradient>
                </defs>
                <XAxis 
                  dataKey="time" 
                  axisLine={false} 
                  tickLine={false}
                  tick={{ fontSize: 12, fill: '#6B7280' }}
                />
                <YAxis hide />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'white', 
                    border: '2px solid #111827',
                    borderRadius: '12px',
                    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)'
                  }} 
                />
                <Area 
                  type="monotone" 
                  dataKey="users" 
                  stroke="#3B82F6" 
                  fill="url(#colorActivity)" 
                  strokeWidth={3}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Performance Trend */}
          <div className="bg-white rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-gradient-to-br from-green-500 to-emerald-600 text-white rounded-lg">
                <TrendingUp className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">Performance Trend</h2>
                <p className="text-sm text-gray-600">Monthly progression</p>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={performanceData}>
                <XAxis 
                  dataKey="month" 
                  axisLine={false} 
                  tickLine={false}
                  tick={{ fontSize: 12, fill: '#6B7280' }}
                />
                <YAxis hide />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'white', 
                    border: '2px solid #111827',
                    borderRadius: '12px',
                    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)'
                  }} 
                />
                <Line 
                  type="monotone" 
                  dataKey="score" 
                  stroke="#10B981" 
                  strokeWidth={4}
                  dot={{ fill: '#10B981', strokeWidth: 2, r: 6 }}
                  activeDot={{ r: 8, fill: '#059669' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

        </div>

        {/* Interactive Regional Heatmap */}
        <div className="bg-white rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300">
          <div className="flex items-center gap-3 mb-8">
            <div className="p-2 bg-gradient-to-br from-pink-500 to-rose-600 text-white rounded-lg">
              <MapPin className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">Language heat map</h2>
              <p className="text-sm text-gray-600">Regional engagement overview</p>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {regionData.map((region, index) => (
              <div key={region.name} className="group relative">
                <div className="absolute inset-0 opacity-0 group-hover:opacity-20 transition-opacity duration-300 rounded-xl blur-lg" style={{backgroundColor: region.color}}></div>
                <div className="relative bg-gradient-to-br from-gray-50 to-white border border-gray-200 rounded-xl p-6 hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-gray-900">{region.name}</h3>
                    <div className="flex items-center gap-2">
                      {getTrendIcon(region.trend)}
                      <span className="text-sm font-bold" style={{color: region.color}}>
                        {region.value}%
                      </span>
                    </div>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-1000 ease-out"
                      style={{ 
                        width: `${region.value}%`,
                        backgroundColor: region.color
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Enhanced Engagement & Videos */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Colorful Engagement Chart */}
          <div className="bg-white rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 text-white rounded-lg">
                <Eye className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">Engagement Mix</h2>
                <p className="text-sm text-gray-600">Content interaction breakdown</p>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={engagementStats}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={90}
                  paddingAngle={3}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {engagementStats.map((entry, index) => (
                    <Cell key={index} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'white', 
                    border: '2px solid #111827',
                    borderRadius: '12px',
                    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)'
                  }} 
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Video Management */}
          <div className="bg-gradient-to-br from-purple-50 via-white to-pink-50 rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-600 text-white rounded-lg">
                <Play className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">Video Library</h2>
                <p className="text-sm text-gray-600">Content management hub</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-6 mb-6">
              <div className="bg-white/80 backdrop-blur-sm border border-gray-200 rounded-xl p-4 text-center">
                <div className="text-3xl font-bold text-blue-600 mb-2">{videoStats.uploaded}</div>
                <div className="text-sm text-gray-600">Total Uploaded</div>
              </div>
              <div className="bg-white/80 backdrop-blur-sm border border-gray-200 rounded-xl p-4 text-center">
                <div className="text-3xl font-bold text-orange-600 mb-2">{videoStats.toBeVerified}</div>
                <div className="text-sm text-gray-600">Pending Review</div>
              </div>
            </div>
            <button
              onClick={nav('/uploadContent')}
              
              className="w-full py-3 rounded-xl font-medium text-xl border-1 text-black duration-300 shadow-lg hover:shadow-xl"
            >
              Manage Uploads
            </button>
          </div>

        </div>

        {/* Enhanced Complaints & Course Progress */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Complaints with Severity */}
          <div className="bg-white rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-gradient-to-br from-red-500 to-pink-600 text-white rounded-lg">
                <AlertCircle className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">Recent Issues</h2>
                <p className="text-sm text-gray-600">User feedback & support</p>
              </div>
            </div>
            <div className="space-y-4">
              {complaints.map((complaint, index) => (
                <div key={index} className="group bg-gradient-to-r from-gray-50 to-white border border-gray-200 rounded-xl p-4 hover:shadow-md transition-all duration-300">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h4 className="font-semibold text-gray-900">{complaint.user}</h4>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          complaint.severity === 'high' ? 'bg-red-100 text-red-800' :
                          complaint.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-green-100 text-green-800'
                        }`}>
                          {complaint.severity}
                        </span>
                      </div>
                      <p className="text-gray-700 text-sm mb-2">{complaint.issue}</p>
                      <p className="text-xs text-gray-500">{complaint.time}</p>
                    </div>
                    <button className="opacity-0 group-hover:opacity-100 transition-opacity bg-blue-600 text-white px-3 py-1 rounded-lg text-xs font-medium hover:bg-blue-700">
                      Visit
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Course Progress */}
          <div className="bg-gradient-to-br from-green-50 via-white to-emerald-50 rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-gradient-to-br from-green-500 to-emerald-600 text-white rounded-lg">
                <BookOpen className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">Learning Progress</h2>
                <p className="text-sm text-gray-600">Course completion tracking</p>
              </div>
            </div>
            
            <div className="text-center mb-6">
              <div className="relative inline-block">
                <div className="w-32 h-32 rounded-full border-8 border-gray-200 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-gray-900">{courseCompletion.percentage}%</div>
                    <div className="text-xs text-gray-600">Complete</div>
                  </div>
                </div>
                <div 
                  className="absolute top-0 left-0 w-32 h-32 rounded-full border-8 border-transparent border-t-green-500 transform transition-all duration-1000"
                  style={{ 
                    transform: `rotate(${(courseCompletion.percentage / 100) * 360}deg)`,
                    borderTopColor: '#10B981'
                  }}
                ></div>
              </div>
            </div>
            
            <div className="bg-white/80 backdrop-blur-sm border border-gray-200 rounded-xl p-4 text-center">
              <div className="text-2xl font-bold text-green-600 mb-1">{courseCompletion.totalCompleted}</div>
              <div className="text-sm text-gray-600">Users Completed</div>
            </div>
            
            <button
              onClick={handleDownload}
              className="w-full mt-6 bg-gradient-to-r from-green-600 to-emerald-600 text-white py-3 rounded-xl font-medium hover:from-green-700 hover:to-emerald-700 transition-all duration-300 shadow-lg hover:shadow-xl flex items-center justify-center gap-2"
            >
              <Download className="w-4 h-4" />
              Download Report
            </button>
          </div>

        </div>

      </div>
    </div>
  );
};

export default Dashboard;