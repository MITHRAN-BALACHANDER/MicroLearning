// src/store/AnalyticsSlice.js
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

//  Replace this later with your real API base
const API_BASE = 'https://your-backend-api.com';

export const fetchAnalyticsData = createAsyncThunk(
  'analytics/fetchAll',
  async () => {
    const response = await fetch(`${API_BASE}/analytics-data`);
    const data = await response.json();
    return data;
  }
);

//  Dummy initial state
const initialState = {
  testStats: [
    { name: '5/5', value: 23.5 },
    { name: '4/5', value: 53.5 },
    { name: '3/5', value: 13.5 },
    { name: '2/5', value: 5.5 },
    { name: '1/5', value: 4.0 },
  ],
  chartData: Array.from({ length: 30 }, (_, i) => ({
    date: `Day ${i + 1}`,
    value: Math.floor(Math.random() * 20) + 1,
  })),
  topPerformers: [
    { name: 'Sahana', status: 'Online', rating: 4.3 },
    { name: 'Sahana', status: 'Online', rating: 4.7 },
    { name: 'Sahana', status: '2 minutes ago', rating: 4.4 },
  ],
  loading: false,
  error: null,
};

const analyticsSlice = createSlice({
  name: 'analytics',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchAnalyticsData.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchAnalyticsData.fulfilled, (state, action) => {
        // Replace with: const { chartData, testStats, topPerformers } = action.payload;
        state.chartData = initialState.chartData;
        state.testStats = initialState.testStats;
        state.topPerformers = initialState.topPerformers;
        state.loading = false;
      })
      .addCase(fetchAnalyticsData.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      });
  },
});

export default analyticsSlice.reducer;
// .addCase(fetchAnalyticsData.fulfilled, (state, action) => {
//   state.chartData = initialState.chartData; // Replace with: action.payload.chartData
//   state.testStats = initialState.testStats; // Replace with: action.payload.testStats
//   state.topPerformers = initialState.topPerformers; // Replace with: action.payload.topPerformers
// });
