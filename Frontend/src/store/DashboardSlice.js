import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

// Optional: Async Thunks if data is fetched from backend
export const fetchDashboardData = createAsyncThunk(
  'dashboard/fetchDashboardData',
  async () => {
    // const res = await fetch('/api/dashboard');
    // return await res.json();

    // Placeholder static data for now
    return {
      activeUsers: [
        { name: "Yesterday", users: 120 },
        { name: "Today", users: 150 },
      ],
      engagementStats: [
        { name: "Videos", value: 45, color: "#FF6B6B" },
        { name: "Tests", value: 30, color: "#4ECDC4" },
        { name: "Discussions", value: 15, color: "#45B7D1" },
        { name: "Downloads", value: 10, color: "#FFA07A" }
      ],
      videoStats: { uploaded: 234, toBeVerified: 12 },
      courseCompletion: { totalCompleted: 1847, percentage: 78 },
      regionData: [
        { name: "Tamil", value: 85, trend: "up", color: "#FF6B6B" },
        { name: "English", value: 72, trend: "down", color: "#4ECDC4" },
        { name: "Kannada", value: 94, trend: "up", color: "#45B7D1" },
        { name: "Hindi", value: 45, trend: "stable", color: "#FFA07A" },
        { name: "Malayalam", value: 38, trend: "up", color: "#98D8C8" },
        { name: "Telugu", value: 56, trend: "down", color: "#F7DC6F" }
      ],
      complaints: [
        { user: "Sahna", issue: "Video playback issues", time: "2h ago", severity: "high" },
        { user: "Sahana", issue: "Login problems", time: "4h ago", severity: "medium" },
        { user: "Sahana", issue: "Course content missing", time: "6h ago", severity: "low" }
      ],
      activityData: [
        { time: "6AM", users: 23, engagement: 45 },
        { time: "9AM", users: 89, engagement: 78 },
        { time: "12PM", users: 156, engagement: 92 },
        { time: "3PM", users: 134, engagement: 87 },
        { time: "6PM", users: 98, engagement: 65 },
        { time: "9PM", users: 67, engagement: 54 }
      ],
      performanceData: [
        { month: "Jan", score: 85 },
        { month: "Feb", score: 88 },
        { month: "Mar", score: 92 },
        { month: "Apr", score: 89 },
        { month: "May", score: 94 },
        { month: "Jun", score: 96 }
      ]
    };
  }
);

const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState: {
    activeUsers: [],
    engagementStats: [],
    videoStats: {},
    courseCompletion: {},
    regionData: [],
    complaints: [],
    activityData: [],
    performanceData: [],
    status: 'idle'
  },
  reducers: {
    // You can define update actions here for real-time update if needed
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchDashboardData.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchDashboardData.fulfilled, (state, action) => {
        Object.assign(state, action.payload);
        state.status = 'succeeded';
      })
      .addCase(fetchDashboardData.rejected, (state) => {
        state.status = 'failed';
      });
  },
});

export default dashboardSlice.reducer;
