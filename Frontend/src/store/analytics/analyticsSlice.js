import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  chartData: [
    { date: "Jan 1", value: 145, previous: 120 },
    { date: "Jan 2", value: 162, previous: 135 },
    { date: "Jan 3", value: 178, previous: 150 },
    { date: "Jan 4", value: 189, previous: 165 },
    { date: "Jan 5", value: 203, previous: 180 },
    { date: "Jan 6", value: 218, previous: 195 },
    { date: "Jan 7", value: 235, previous: 210 },
  ],
  testStats: [
    { name: "Excellent (90-100)", value: 285, percentage: 35 },
    { name: "Good (80-89)", value: 412, percentage: 42 },
    { name: "Average (70-79)", value: 156, percentage: 18 },
    { name: "Poor (0-69)", value: 47, percentage: 5 },
  ],
  topPerformers: [
    { name: "Sahana", rating: "98.5%", tests: 24 },
    { name: "Sahana", rating: "96.2%", tests: 22 },
    { name: "Sahana", rating: "94.8%", tests: 26 },
    { name: "Sahana", rating: "92.3%", tests: 21 },
  ],
  pieData: [
    { name: "Completed", value: 68, color: "#10B981" },
    { name: "In Progress", value: 22, color: "#F59E0B" },
    { name: "Not Started", value: 10, color: "#EF4444" },
  ],
  weeklyData: [
    { day: "Mon", tests: 45, study: 120, active: 89 },
    { day: "Tue", tests: 52, study: 135, active: 94 },
    { day: "Wed", tests: 48, study: 142, active: 87 },
    { day: "Thu", tests: 61, study: 158, active: 102 },
    { day: "Fri", tests: 38, study: 98, active: 76 },
    { day: "Sat", tests: 29, study: 88, active: 65 },
    { day: "Sun", tests: 34, study: 92, active: 71 },
  ],
};

const analyticsSlice = createSlice({
  name: 'analytics',
  initialState,
  reducers: {
    // Later use these actions to update state from backend
    setChartData: (state, action) => { state.chartData = action.payload },
    setTestStats: (state, action) => { state.testStats = action.payload },
    setTopPerformers: (state, action) => { state.topPerformers = action.payload },
    setPieData: (state, action) => { state.pieData = action.payload },
    setWeeklyData: (state, action) => { state.weeklyData = action.payload },
  },
});

export const {
  setChartData,
  setTestStats,
  setTopPerformers,
  setPieData,
  setWeeklyData,
} = analyticsSlice.actions;

export default analyticsSlice.reducer;
