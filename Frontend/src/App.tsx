import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import DashboardPage from './pages/Dashboard/DashboardPage';
import GeneratePage from './pages/Generate/GeneratePage';
import EnhancePage from './pages/Enhance/EnhancePage';
import MigratePage from './pages/Migrate/MigratePage';
import AnalyticsPage from './pages/Analytics/AnalyticsPage';

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/generate" element={<GeneratePage />} />
        <Route path="/enhance" element={<EnhancePage />} />
        <Route path="/migrate" element={<MigratePage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
      </Routes>
    </Layout>
  );
}
