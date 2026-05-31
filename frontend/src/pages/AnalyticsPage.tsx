import { AlertCircle, CalendarPlus, CalendarDays, Check, Pencil, PieChart as PieIcon, Trash2 } from 'lucide-react';
import { useState } from 'react';
import { Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { EmptyState } from '../components/EmptyState';
import { StatCard } from '../components/StatCard';
import { StatusPill } from '../components/StatusPill';
import { useAppContext } from '../context/AppContext';
import { useAsync } from '../hooks/useAsync';
import { api, formatApiError } from '../services/api';
import type { AcademicEvent } from '../types';

const colors = ['#2563eb', '#0f9f8f', '#e05d44', '#d89418', '#7c3aed', '#475467'];

export function AnalyticsPage() {
  const { userId } = useAppContext();
  const { accessToken, googleAccessToken, signInWithGoogle } = useAppContext();
  const analytics = useAsync(() => (userId ? api.analytics(userId, accessToken) : Promise.resolve(null)), [userId, accessToken]);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [editingEvent, setEditingEvent] = useState<AcademicEvent | null>(null);
  const [editMessage, setEditMessage] = useState<string | null>(null);

  if (!userId) return <EmptyState icon={AlertCircle} title="Add your user UUID" body="Paste your Supabase Auth user UUID in the header before loading analytics." />;
  if (analytics.error) return <EmptyState icon={AlertCircle} title="Analytics failed" body={formatApiError(analytics.error)} />;

  const summary = analytics.data;
  const distribution = Object.entries(
    (summary?.upcoming_deadlines ?? []).reduce<Record<string, number>>((acc, event) => {
      acc[event.event_type] = (acc[event.event_type] ?? 0) + 1;
      return acc;
    }, {}),
  ).map(([name, value]) => ({ name, value }));

  async function syncCalendar() {
    if (!googleAccessToken) {
      await signInWithGoogle();
      return;
    }
    setSyncing(true);
    setSyncMessage(null);
    try {
      const eventIds = (summary?.upcoming_deadlines ?? []).map((event) => event.id);
      if (!eventIds.length) {
        setSyncMessage('No upcoming extracted deadlines to sync.');
        return;
      }
      const result = await api.syncCalendar(userId, googleAccessToken, eventIds, accessToken);
      setSyncMessage(`Synced ${result.synced_count} of ${eventIds.length} visible deadlines to Google Calendar${result.failed.length ? `; ${result.failed.length} failed.` : '.'}`);
    } catch (error) {
      setSyncMessage(formatApiError(error));
    } finally {
      setSyncing(false);
    }
  }

  async function verifyEvent(eventId: string) {
    await api.updateEvent(userId, eventId, { verification_status: 'verified', confidence_score: 1 }, accessToken);
    await analytics.reload();
  }

  async function deleteEvent(eventId: string, title: string) {
    if (!window.confirm(`Delete extracted event "${title}"?`)) return;
    await api.deleteEvent(userId, eventId, accessToken);
    await analytics.reload();
  }

  async function saveEditedEvent(event: AcademicEvent) {
    setEditMessage(null);
    try {
      await api.updateEvent(
        userId,
        event.id,
        {
          title: event.title,
          event_type: event.event_type,
          description: event.description || null,
          due_at: event.due_at || null,
          grading_weight: event.grading_weight ?? null,
          estimated_hours: event.estimated_hours ?? null,
          confidence_score: event.confidence_score ?? null,
          verification_status: event.verification_status,
        },
        accessToken,
      );
      setEditingEvent(null);
      await analytics.reload();
    } catch (error) {
      setEditMessage(formatApiError(error));
    }
  }

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-line bg-white p-5 shadow-soft">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-lg font-semibold">Google Calendar sync</h2>
            <p className="mt-1 text-sm text-muted">Send extracted deadlines to your primary Google Calendar.</p>
          </div>
          <button onClick={syncCalendar} disabled={syncing} className="flex items-center justify-center gap-2 rounded-lg bg-brand px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">
            <CalendarPlus size={17} />
            {syncing ? 'Syncing...' : googleAccessToken ? 'Sync deadlines' : 'Connect Google Calendar'}
          </button>
        </div>
        {syncMessage && <p className="mt-3 rounded-lg bg-app px-3 py-2 text-sm text-muted">{syncMessage}</p>}
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <StatCard label="Upcoming events" value={`${summary?.upcoming_deadlines.length ?? 0}`} icon={CalendarDays} accent="#0f9f8f" />
        <StatCard label="Assignments" value={`${summary?.assignment_count ?? 0}`} icon={CalendarDays} accent="#2563eb" />
        <StatCard label="Exams" value={`${summary?.exam_count ?? 0}`} icon={PieIcon} accent="#e05d44" />
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <ChartPanel title="Estimated study hours">
          {summary?.workload_by_week.length ? (
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={summary.workload_by_week}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="week_start" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="estimated_hours" fill="#2563eb" radius={[6, 6, 0, 0]} />
                <Bar dataKey="deadline_count" fill="#0f9f8f" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <EmptyState icon={CalendarDays} title="No workload data" body="Extract deadlines to generate workload charts." />}
        </ChartPanel>

        <ChartPanel title="Event distribution">
          {distribution.length ? (
            <ResponsiveContainer width="100%" height={320}>
              <PieChart>
                <Pie data={distribution} dataKey="value" nameKey="name" outerRadius={110} label>
                  {distribution.map((entry, index) => <Cell key={entry.name} fill={colors[index % colors.length]} />)}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : <EmptyState icon={PieIcon} title="No event distribution" body="Run deadline extraction on a syllabus to see event categories." />}
        </ChartPanel>
      </section>

      <section className="rounded-lg border border-line bg-white p-5 shadow-soft">
        <h2 className="text-lg font-semibold">Extracted events</h2>
        <div className="mt-4 max-h-[430px] overflow-auto pr-1">
          <table className="w-full min-w-[720px] border-separate border-spacing-0 text-left text-sm">
            <thead className="text-muted">
              <tr>
                <th className="border-b border-line py-3 font-medium">Title</th>
                <th className="border-b border-line py-3 font-medium">Course</th>
                <th className="border-b border-line py-3 font-medium">Type</th>
                <th className="border-b border-line py-3 font-medium">Due</th>
                <th className="border-b border-line py-3 font-medium">Weight</th>
                <th className="border-b border-line py-3 font-medium">Status</th>
                <th className="border-b border-line py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {summary?.upcoming_deadlines.map((event) => (
                <tr key={event.id}>
                  <td className="border-b border-line py-3 pr-4 font-medium">{event.title}</td>
                  <td className="border-b border-line py-3 pr-4 text-muted">
                    <div className="flex items-center gap-2">
                      <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: event.course_color ?? '#667085' }} />
                      <span>{event.course_code || event.course_name || 'No course'}</span>
                    </div>
                  </td>
                  <td className="border-b border-line py-3 pr-4 text-muted">{event.event_type}</td>
                  <td className="border-b border-line py-3 pr-4 text-muted">{event.due_at ? new Date(event.due_at).toLocaleString() : 'Unknown'}</td>
                  <td className="border-b border-line py-3 pr-4 text-muted">{event.grading_weight == null ? 'N/A' : `${event.grading_weight}%`}</td>
                  <td className="border-b border-line py-3 pr-4"><StatusPill value={event.verification_status} /></td>
                  <td className="border-b border-line py-3 pr-4">
                    <div className="flex items-center gap-2">
                      <button onClick={() => setEditingEvent(event)} className="grid h-8 w-8 place-items-center rounded-lg border border-line text-muted hover:text-ink" title="Edit event"><Pencil size={15} /></button>
                      <button onClick={() => verifyEvent(event.id)} className="grid h-8 w-8 place-items-center rounded-lg border border-line text-muted hover:text-emerald-700" title="Mark verified"><Check size={15} /></button>
                      <button onClick={() => deleteEvent(event.id, event.title)} className="grid h-8 w-8 place-items-center rounded-lg border border-line text-muted hover:border-red-200 hover:bg-red-50 hover:text-red-700" title="Delete event"><Trash2 size={15} /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      {editingEvent && (
        <EditEventPanel
          event={editingEvent}
          message={editMessage}
          onChange={setEditingEvent}
          onCancel={() => {
            setEditingEvent(null);
            setEditMessage(null);
          }}
          onSave={saveEditedEvent}
        />
      )}
    </div>
  );
}

function EditEventPanel({
  event,
  message,
  onChange,
  onCancel,
  onSave,
}: {
  event: AcademicEvent;
  message: string | null;
  onChange: (event: AcademicEvent) => void;
  onCancel: () => void;
  onSave: (event: AcademicEvent) => Promise<void>;
}) {
  const parsed = event.due_at ? new Date(event.due_at) : null;
  const dateValue = parsed && !Number.isNaN(parsed.getTime()) ? toDateInputValue(parsed) : '';
  const timeValue = parsed && !Number.isNaN(parsed.getTime()) ? toTimeInputValue(parsed) : '23:59';

  function setDueAt(nextDate: string, nextTime: string) {
    if (!nextDate) {
      onChange({ ...event, due_at: null });
      return;
    }
    onChange({ ...event, due_at: new Date(`${nextDate}T${nextTime || '23:59'}:00`).toISOString() });
  }

  return (
    <section className="fixed inset-0 z-30 grid place-items-center bg-ink/30 px-4 py-6">
      <div className="max-h-[92vh] w-full max-w-3xl overflow-y-auto rounded-lg border border-line bg-white p-5 shadow-soft">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold">Edit extracted event</h2>
            <p className="mt-1 text-sm text-muted">Review every field before this event affects analytics or calendar sync.</p>
          </div>
          <button onClick={onCancel} className="rounded-lg border border-line px-3 py-2 text-sm text-muted hover:text-ink">Close</button>
        </div>

        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <label className="block text-sm font-medium text-ink md:col-span-2">
            Title
            <input value={event.title} onChange={(e) => onChange({ ...event, title: e.target.value })} className="mt-2 w-full rounded-lg border border-line px-3 py-2 outline-none focus:border-brand" />
          </label>

          <label className="block text-sm font-medium text-ink">
            Type
            <select value={event.event_type} onChange={(e) => onChange({ ...event, event_type: e.target.value as AcademicEvent['event_type'] })} className="mt-2 w-full rounded-lg border border-line px-3 py-2 outline-none focus:border-brand">
              {['assignment', 'quiz', 'exam', 'project', 'reading', 'lecture', 'other'].map((type) => <option key={type} value={type}>{type}</option>)}
            </select>
          </label>

          <label className="block text-sm font-medium text-ink">
            Verification status
            <select value={event.verification_status} onChange={(e) => onChange({ ...event, verification_status: e.target.value as AcademicEvent['verification_status'] })} className="mt-2 w-full rounded-lg border border-line px-3 py-2 outline-none focus:border-brand">
              {['pending', 'verified', 'flagged', 'rejected'].map((status) => <option key={status} value={status}>{status}</option>)}
            </select>
          </label>

          <div className="md:col-span-2">
            <p className="text-sm font-medium text-ink">Due date and time</p>
            <div className="mt-2 flex flex-wrap gap-2">
              <input type="date" value={dateValue} onChange={(e) => setDueAt(e.target.value, timeValue)} className="rounded-lg border border-line px-3 py-2 outline-none focus:border-brand" />
              <input type="time" value={timeValue} onChange={(e) => setDueAt(dateValue, e.target.value)} className="rounded-lg border border-line px-3 py-2 outline-none focus:border-brand" />
              <button type="button" onClick={() => onChange({ ...event, due_at: null })} className="rounded-lg border border-line px-3 py-2 text-sm text-muted hover:text-ink">Clear date</button>
            </div>
          </div>

          <label className="block text-sm font-medium text-ink">
            Grading weight (%)
            <input type="number" min="0" max="100" step="0.01" value={event.grading_weight ?? ''} onChange={(e) => onChange({ ...event, grading_weight: e.target.value ? Number(e.target.value) : null })} className="mt-2 w-full rounded-lg border border-line px-3 py-2 outline-none focus:border-brand" />
          </label>

          <label className="block text-sm font-medium text-ink">
            Estimated hours
            <input type="number" min="0" max="200" step="0.5" value={event.estimated_hours ?? ''} onChange={(e) => onChange({ ...event, estimated_hours: e.target.value ? Number(e.target.value) : null })} className="mt-2 w-full rounded-lg border border-line px-3 py-2 outline-none focus:border-brand" />
          </label>

          <label className="block text-sm font-medium text-ink md:col-span-2">
            Description / notes
            <textarea value={event.description ?? ''} onChange={(e) => onChange({ ...event, description: e.target.value })} rows={4} className="mt-2 w-full rounded-lg border border-line px-3 py-2 outline-none focus:border-brand" />
          </label>
        </div>

        {message && <p className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{message}</p>}

        <div className="mt-5 flex flex-wrap justify-end gap-2">
          <button onClick={onCancel} className="rounded-lg border border-line px-4 py-2 text-sm text-muted hover:text-ink">Cancel</button>
          <button onClick={() => onSave(event)} className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white">Save event</button>
        </div>
      </div>
    </section>
  );
}

function toDateInputValue(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function toTimeInputValue(date: Date) {
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${hours}:${minutes}`;
}

function ChartPanel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-line bg-white p-5 shadow-soft">
      <h2 className="mb-4 text-lg font-semibold">{title}</h2>
      {children}
    </div>
  );
}
