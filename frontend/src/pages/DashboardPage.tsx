import { AlertCircle, ArrowRight, Bot, CalendarDays, CheckCircle2, Clock, FileText } from 'lucide-react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Page } from '../App';
import { EmptyState } from '../components/EmptyState';
import { StatCard } from '../components/StatCard';
import { StatusPill } from '../components/StatusPill';
import { useAppContext } from '../context/AppContext';
import { useAsync } from '../hooks/useAsync';
import { api, formatApiError } from '../services/api';

export function DashboardPage({ onNavigate }: { onNavigate: (page: Page) => void }) {
  const { userId } = useAppContext();
  const { accessToken } = useAppContext();
  const analytics = useAsync(() => (userId ? api.analytics(userId, accessToken) : Promise.resolve(null)), [userId, accessToken]);
  const documents = useAsync(() => (userId ? api.listDocuments(userId, accessToken) : Promise.resolve([])), [userId, accessToken]);

  if (!userId) {
    return <EmptyState icon={AlertCircle} title="Sign in to Study Buddy" body="Use Google sign-in to load your courses, documents, chat, and analytics." />;
  }

  const summary = analytics.data;
  const docs = documents.data ?? [];
  const processedDocs = docs.filter((doc) => doc.status === 'processed').length;
  const errorMessage = analytics.error || documents.error ? formatApiError(analytics.error ?? documents.error) : null;

  return (
    <div className="space-y-6">
      {errorMessage && <ErrorBanner message={errorMessage} />}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Upcoming deadlines" value={`${summary?.upcoming_deadlines.length ?? 0}`} icon={CalendarDays} accent="#2563eb" />
        <StatCard label="Assignments" value={`${summary?.assignment_count ?? 0}`} icon={CheckCircle2} accent="#0f9f8f" />
        <StatCard label="Exams" value={`${summary?.exam_count ?? 0}`} icon={Clock} accent="#e05d44" />
        <StatCard label="Processed PDFs" value={`${processedDocs}`} icon={FileText} accent="#d89418" />
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
        <div className="rounded-lg border border-line bg-white p-5 shadow-soft">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold">Weekly workload</h2>
              <p className="text-sm text-muted">Deadlines and estimated hours from extracted academic events.</p>
            </div>
            <button onClick={() => onNavigate('analytics')} className="flex items-center gap-2 rounded-lg border border-line px-3 py-2 text-sm text-muted hover:text-ink">
              <ArrowRight size={16} />
              Analytics
            </button>
          </div>
          <div className="h-72">
            {summary?.workload_by_week.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={summary.workload_by_week}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="week_start" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="estimated_hours" fill="#2563eb" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState icon={CalendarDays} title="No workload yet" body="Extract deadlines from a syllabus to populate weekly workload analytics." />
            )}
          </div>
        </div>

        <div className="rounded-lg border border-line bg-white p-5 shadow-soft">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Next deadlines</h2>
            <button onClick={() => onNavigate('chat')} className="grid h-9 w-9 place-items-center rounded-lg border border-line text-muted hover:text-ink" title="Open AI chat">
              <Bot size={17} />
            </button>
          </div>
          <div className="space-y-3">
            {summary?.upcoming_deadlines.length ? (
              summary.upcoming_deadlines.slice(0, 6).map((event) => (
                <div key={event.id} className="rounded-lg border border-line p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-medium">{event.title}</p>
                      <p className="mt-1 text-sm text-muted">{event.due_at ? new Date(event.due_at).toLocaleString() : 'No date found'}</p>
                    </div>
                    <StatusPill value={event.verification_status} />
                  </div>
                </div>
              ))
            ) : (
              <EmptyState icon={Clock} title="No deadlines extracted" body="Upload a syllabus and run deadline extraction to fill this list." />
            )}
          </div>
        </div>
      </section>
    </div>
  );
}

function ErrorBanner({ message }: { message: string }) {
  return <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{message}</div>;
}
