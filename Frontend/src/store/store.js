// src/store.js
import { configureStore } from '@reduxjs/toolkit';
import dashboardReducer from './DashboardSlice'
import analyticsReducer from './AnalyticsSlice'

const store = configureStore({
  reducer: {
    content: dashboardReducer,
    analytics: analyticsReducer,
  },
});

export default store;
