import React, { useEffect } from "react";
import { useSelector, useDispatch } from "react-redux";
import { useNavigate } from "react-router-dom";
import { Download } from "@mui/icons-material";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from "recharts";
import { fetchDashboardData, fetchTestResults } from '../store/DashboardSlice'
import video from '../assets/video.png';

import { downloadExcel } from "../utils/excelDownload";

const COLORS = ["#FE7F2D", "#212223"];

const Dashboard = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const {
    activeUsers,
    engagementStats,
    testResults,
    videoStats,
    courseCompletion
  } = useSelector((state) => state.content);

  useEffect(() => {
    dispatch(fetchDashboardData());
    dispatch(fetchTestResults());
  }, [dispatch]);

  const handleDownload = () => {
    downloadExcel(testResults, 'UserTestResults');
  };

  return (
    <div className="flex items-center m-6 mt-15 flex-col w-full gap-6 bg-gray-50 min-h-screen">
      <div className="flex flex-wrap gap-6 justify-between items-start p-5">

        <div className="bg-white text-black p-6 rounded-2xl shadow-md w-full md:w-[48%]">
          <h2 className="text-lg font-semibold"> Active Users</h2>
          <p className="text-sm text-gray-400 mb-2">Past 24hrs vs Now</p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={activeUsers}>
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="users" fill="#212223" />
            </BarChart>
          </ResponsiveContainer>
        </div>

      
        <div className="bg-white p-6 rounded-2xl flex justify-between items-center shadow-md pt-15 pb-10 pl-8 w-full md:w-[48%]">
          <div>
            <h2 className="text-lg font-semibold mb-4">Videos</h2>
            <p className="text-md">Uploaded: <span className="font-bold">{videoStats.uploaded}</span></p>
            <p className="text-md mb-2">To be Verified: <span className="font-bold">{videoStats.toBeVerified}</span></p>
            <p>To verify videos</p>
            <button
              className="bg-gray-100 rounded p-2 mt-4 hover:bg-gray-200"
              onClick={() => navigate('/uploadContent')}
            >
              Click here..
            </button>
          </div>
          <div><img className="h-auto w-40" src={video} alt="" /></div>
        </div>
      </div>

      {/* Engagement + Excel */}
      <div className="flex flex-wrap gap-6 justify-between items-stretch p-5">
        {/* Engagement Pie Chart */}
        <div className="bg-white p-5 rounded-2xl shadow-md w-full md:w-[48%]">
          <h2 className="text-lg font-semibold mb-4">Engagement</h2>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={engagementStats}
                dataKey="value"
                nameKey="name"
                outerRadius={60}
                fill="#8884d8"
                label
              >
                {engagementStats.map((entry, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Download Test Results */}
        <div className="bg-white p-5 rounded-2xl shadow-md w-full md:w-[48%] cursor-pointer flex flex-col items-center justify-between">
          <h2 className="text-xl font-semibold mb-2">
            <Download /> Test Results
          </h2>
          <p className="text-gray-600 font-semibold text-lg">
            Click to download a detailed Excel report containing the test scores, names, and performance summaries of users who have taken the assessments.
          </p>
          <button
            className="bg-gray-50 rounded p-3 mt-3 flex hover:bg-gray-100 transition"
            onClick={handleDownload}
          >
            Click here
          </button>
        </div>
      </div>

      <div className="bg-white min-w-[90%] p-3  rounded-2xl shadow-md col-span-1 md:col-span-2">
        <h2 className="text-lg font-semibold mb-4">Course Completion</h2>
        <p className="text-md mb-2">Total Users Completed: <span className="font-bold">{courseCompletion.totalCompleted}</span></p>
        <div className="bg-gray-200 rounded-full h-4 w-full">
          <div className="bg-green-500 h-4 rounded-full" style={{ width: `${courseCompletion.percentage}%` }}></div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
