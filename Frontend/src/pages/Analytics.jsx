import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar
} from 'recharts';
import { CircleGauge } from 'lucide-react';
import { fetchAnalyticsData } from '../store/AnalyticsSlice';
import { downloadExcel } from '../utils/excelDownload';

export default function Analytics() {
  const dispatch = useDispatch();
  const { chartData, testStats, topPerformers } = useSelector((state) => state.analytics);
const { testResults } = useSelector((state) => state.analytics);
  useEffect(() => {
    dispatch(fetchAnalyticsData());
  }, [dispatch]);

  return (
    <div className="p-6 m-5 mt-15 flex flex-col w-full pb-10 gap-6 bg-gray-50 min-h-screen">
     
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {['Test Performance', 'Users', 'Videos/Time', 'Feedback'].map((label, i) => (
          <div key={i} className="bg-indigo-100 rounded-xl p-4 flex flex-col items-center shadow">
            <CircleGauge className="text-indigo-600 w-10 h-10" />
            <p className="font-semibold mt-2">{label}</p>
            <p className="text-2xl font-bold text-indigo-800">0</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl p-4 shadow">
          <h2 className="text-center text-lg font-semibold mb-4">Learners taking test</h2>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={chartData}>
              <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#94a3b8" />
              <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" />
              <Tooltip
                contentStyle={{ backgroundColor: '#ecfeff', borderColor: '#06b6d4' }}
                labelStyle={{ fontWeight: 'bold' }}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#06b6d4"
                strokeWidth={3}
                dot={{ stroke: '#06b6d4', strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
          <div className='mt-10'>This chart shows the number of learners taking the test over the past 30 days.</div>
        </div>

        <div className="bg-gray-100 rounded-xl p-4 shadow">
          <h2 className="text-center text-lg font-medium mb-2">Marks obtained</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={testStats}>
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#333" />
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-3 space-y-2">
            {testStats.map((item, i) => (
              <div key={i} className="flex justify-between bg-white rounded-lg px-4 py-2 text-sm font-medium">
                <span>{item.name}</span>
                <span>{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
  <div className="bg-gray-100 rounded-xl p-6 flex flex-col justify-center items-center shadow">
    <p className="text-lg mb-4 text-center">Click here to download test scores</p>
    <button
      className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700"
      onClick={() => downloadExcel(testStats, 'TestScores')} // or use testResults if you have that
    >
      Download
    </button>
  </div>


        <div className="bg-white rounded-xl p-6 shadow">
          <h2 className="text-lg font-semibold mb-4">Top performers</h2>
          {topPerformers.map((user, i) => (
            <div key={i} className="flex justify-between items-center border-b py-2">
              <div>
                <p className="font-semibold">{user.name}</p>
                <p className="text-sm text-gray-500">{user.status}</p>
              </div>
              <span className="text-orange-500 font-bold">{user.rating}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
