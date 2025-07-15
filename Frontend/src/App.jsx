import React, { useState } from 'react';
import { Route, Routes } from 'react-router-dom';
import Analytics from './pages/Analytics';
import Feedback from './pages/Feedback';
import Logs from './pages/Logs';
import DisplayUsers from './pages/DisplayUsers';
import UploadContent from './pages/UploadContent';
import Dashboard from './pages/Dashboard';
import Content from './pages/Content';
import ContentDisplay from './pages/ContentDisplay';
import Notfound from './pages/Notfound';
import Sidebar from './components/Sidebar';
import FeedbackDisplay from './pages/FeedbackDisplay';
import Settings from './pages/Settings'
import Test from './pages/Test';
const App = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  return (
    <div className="flex h-screen overflow-hidden poppins-regular">
      {/* Sidebar */}
      <Sidebar isCollapsed={isCollapsed} setIsCollapsed={setIsCollapsed} />

      {/* Main Content */}
      <main
        className={`transition-all duration-300 p-4 flex-1 overflow-auto ${
          isCollapsed ? 'ml-0' : 'ml-64'
        }`}
      >
        <Routes>
          <Route path='/' element={<Dashboard />} />
          <Route path='/contentManagement' element={<ContentDisplay />} />
          <Route path="/content-management/:videoID" element={<Content />} />
          <Route path='/uploadContent' element={<UploadContent />} />
          <Route path='/users' element={<DisplayUsers />} />
          <Route path='/analytics' element={<Analytics />} />
          <Route path='/feedbackDisplay' element={<FeedbackDisplay />} />
          <Route path='/logs' element={<Logs />} />
          <Route path='settings' element={<Settings/>}/>
          <Route path='/*' element={<Notfound />} />
        </Routes>
        <Test/>
 </main>

      </div>
   

      )}
     

export default App;
