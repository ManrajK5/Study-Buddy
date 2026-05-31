import { useState } from 'react';
import { AppProvider } from './context/AppContext';
import { AppLayout } from './layouts/AppLayout';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { ChatPage } from './pages/ChatPage';
import { CoursesPage } from './pages/CoursesPage';
import { DashboardPage } from './pages/DashboardPage';
import { UploadPage } from './pages/UploadPage';

export type Page = 'dashboard' | 'courses' | 'upload' | 'chat' | 'analytics';

export function App() {
  const [page, setPage] = useState<Page>('dashboard');

  return (
    <AppProvider>
      <AppLayout page={page} onPageChange={setPage}>
        {page === 'dashboard' && <DashboardPage onNavigate={setPage} />}
        {page === 'courses' && <CoursesPage />}
        {page === 'upload' && <UploadPage onNavigate={setPage} />}
        {page === 'chat' && <ChatPage />}
        {page === 'analytics' && <AnalyticsPage />}
      </AppLayout>
    </AppProvider>
  );
}
