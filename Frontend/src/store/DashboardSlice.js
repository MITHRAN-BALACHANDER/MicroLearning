import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

//  Placeholder base URL — replace with actual API base when ready
const API_BASE = 'https://your-backend-api.com';

// Async thunk to fetch all dashboard data (active users, engagement, etc.)
export const fetchDashboardData = createAsyncThunk(
  'dashboard/fetchAll',
  async () => {
   
    // const response = await fetch(`${API_BASE}/dashboard-data`);
    // const data = await response.json();
    // return data;

    return {
      activeUsers: [
        { name: "Prev 24hrs", users: 2300 },
        { name: "8th July", users: 2850 },
        { name: "7th July", users: 1950 },
      ],
      engagementStats: [
        { name: "Minutes Played", value: 15368 },
        { name: "Stars", value: 892 },
      ],
      videoStats: {
        uploaded: 120,
        toBeVerified: 14,
      },
      courseCompletion: {
        totalCompleted: 1024,
        percentage: 78,
      }
    };
  }
);

// Async thunk to fetch test results
export const fetchTestResults = createAsyncThunk(
  'dashboard/fetchTestResults',
  async () => {
    // For now, return dummy data directly
    //  REPLACE with this when backend is ready:
    // const response = await fetch(`${API_BASE}/test-results`);
    // const data = await response.json();
    // return data;

    return [
      { name: 'Sahan', videoName: 'cse', score: 92 },
      { name: 'Kavin', videoName: 'cyber', score: 92 },
      { name: 'Mithran', videoName: 'it', score: 88 },
      { name: 'Sajit', videoName: 'ds', score: 74 },
    ];
  }
);

//  Initial Redux state
const initialState = {
  activeUsers: [],
  engagementStats: [],
  testResults: [],
  videoStats: {
    uploaded: 0,
    toBeVerified: 0,
  },
  courseCompletion: {
    totalCompleted: 0,
    percentage: 0,
  },
  loading: false,
  error: null,
};

const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState,
  reducers: {
    // Optional manual overrides
    setVideoStats(state, action) {
      state.videoStats = action.payload;
    },
    setCourseCompletion(state, action) {
      state.courseCompletion = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      //  While loading dashboard data
      .addCase(fetchDashboardData.pending, (state) => {
        state.loading = true;
      })
      
      //  When dashboard data is fetched (dummy or real)
      .addCase(fetchDashboardData.fulfilled, (state, action) => {
        const { activeUsers, engagementStats, videoStats, courseCompletion } = action.payload;
        state.activeUsers = activeUsers;
        state.engagementStats = engagementStats;
        state.videoStats = videoStats;
        state.courseCompletion = courseCompletion;
        state.loading = false;
      })
      
      
      .addCase(fetchDashboardData.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      })





























      
     
      .addCase(fetchTestResults.fulfilled, (state, action) => {
        state.testResults = action.payload;
      });
  },
});

export const { setVideoStats, setCourseCompletion } = dashboardSlice.actions;
export default dashboardSlice.reducer;
