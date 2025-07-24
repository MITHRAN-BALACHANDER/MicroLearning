import React, { useState } from 'react';
import { Route, Routes } from 'react-router-dom';
import Analytics from './pages/Analytics';
// import Feedback from './pages/Feedback';
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
// import Test from './pages/Test';
const App = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const openClosedSidebar = () => {
    setIsCollapsed(!isCollapsed);
    marginLeft: window.innerWidth >= 1024 ? (isCollapsed ? '5rem' : '16rem') : '0'
  };
  return (

    <div className="flex h-screen overflow-hidden poppins-regular">
     
      <Sidebar isCollapsed={isCollapsed} setIsCollapsed={openClosedSidebar} />

     
  <main 
  className="transition-all duration-300 p-4 flex-1 overflow-auto ml-0"
  style={{
    marginLeft: window.innerWidth >= 1024 ? (isCollapsed ? '5rem' : '16rem') : '0'
  
  }}
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
       
 </main>

      </div>
   

      )}
     

export default App;
