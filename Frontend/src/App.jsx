import React from 'react';
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
import Test from './pages/Test';

const App = () => {
  return (
    <>
    <div className="flex h-screen w-full">
       
      <div className="w-[20%]  text-white">
       <Sidebar/>
      </div>

   
      <div className="w-[80%] p-4 flex justify-center  overflow-auto">
        <Routes>
          <Route path='/' element={<Dashboard />} />
          <Route path='/contentManagement' element={<Content />} />
          <Route path='/content-management/:videoID' element={<ContentDisplay />} />
          <Route path='/uploadContent' element={<UploadContent />} />
          <Route path='/users' element={<DisplayUsers />} />
          <Route path='/analytics' element={<Analytics />} />
          <Route path='/feedbackDisplay' element={<FeedbackDisplay />} />
          <Route path='/logs' element={<Logs />} />
          <Route path='/*' element={<Notfound />} />
        </Routes>
      </div> 

    </div>
    </>
  );
};

export default App;
