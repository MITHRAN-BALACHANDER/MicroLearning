import { Route, Routes } from "react-router-dom";

import { DashboardLayout } from "@/app/layouts/dashboard-layout";
import Analytics from "@/pages/Analytics";
import Content from "@/pages/Content";
import ContentDisplay from "@/pages/ContentDisplay";
import Dashboard from "@/pages/Dashboard";
import DisplayUsers from "@/pages/DisplayUsers";
import FeedbackDisplay from "@/pages/FeedbackDisplay";
import Logs from "@/pages/Logs";
import Notfound from "@/pages/Notfound";
import Settings from "@/pages/Settings";
import UploadContent from "@/pages/UploadContent";

function App() {
  return (
    <DashboardLayout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/content-management" element={<ContentDisplay />} />
        <Route path="/content-management/:videoId" element={<Content />} />
        <Route path="/upload-content" element={<UploadContent />} />
        <Route path="/users" element={<DisplayUsers />} />
        <Route path="/feedback" element={<FeedbackDisplay />} />
        <Route path="/logs" element={<Logs />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<Notfound />} />
      </Routes>
    </DashboardLayout>
  );
}

export default App;
