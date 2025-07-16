// src/store/store.js
import { configureStore } from '@reduxjs/toolkit';
import analyticsReducer from './analytics/analyticsSlice';
import dashboardReducer from  './DashboardSlice.js'

const store = configureStore({
  reducer: {
    analytics: analyticsReducer,
    dashboard: dashboardReducer,
  },
});
export default store
