import { AlertCircle, Check, FileText, FileUp, RefreshCw, Sparkles, Trash2, X } from 'lucide-react';
import { FormEvent, useState } from 'react';
import { EmptyState } from '../components/EmptyState';
import { StatusPill } from '../components/StatusPill';
import { useAppContext } from '../context/AppContext';
import { useAsync } from '../hooks/useAsync';
import { api, formatApiError } from '../services/api';
import type { DeadlinePreview, ExtractedEventDraft } from '../types';
import type { Page } from '../App';

export function UploadPage({ onNavigate }: { onNavigate: (page: Page) => void }) {
  const { userId, accessToken } = useAppContext();
  const courses = useAsync(() => (userId ? api.listCourses(userId, accessToken) : Promise.resolve([])), [userId, accessToken]);
  const documents = useAsync(() => (userId ? api.listDocuments(userId, accessToken) : Promise.resolve([])), [userId, accessToken]);
  const [courseId, setCourseId] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [preview, setPreview] = useState<DeadlinePreview | null>(null);

  async function handleUpload(event: FormEvent) {
    event.preventDefault();
    if (!userId || !file) return;
    setBusy(true);
    setMessage(null);
    try {
      const duplicate = documents.data?.find((doc) => doc.file_name === file.name && doc.file_size === file.size && (courseId ? doc.course_id === courseId : !doc.course_id));
      if (duplicate) {
        setMessage(`Duplicate file detected locally: ${duplicate.file_name}. Delete the existing copy first if you want to replace it.`);
        return;
      }
      await api.uploadDocument(userId, courseId || null, file, accessToken);
      setFile(null);
      setMessage('PDF uploaded and processed.');
      await documents.reload();
    } catch (err) {
      setMessage(formatApiError(err));
    } finally {
      setBusy(false);
    }
  }

  async function extract(documentId: string) {
    if (!userId) return;
    setBusy(true);
    setMessage(null);
    try {
      const result = await api.extractDeadlines(userId, documentId, accessToken);
      setMessage(`Extracted ${result.extracted_count} academic events.`);
    } catch (err) {
      setMessage(formatApiError(err));
    } finally {
      setBusy(false);
    }
  }

  async function previewExtraction(documentId: string) {
    if (!userId) return;
    setBusy(true);
    setMessage(null);
    try {
      const result = await api.previewDeadlines(userId, documentId, accessToken);
      setPreview(result);
      setMessage(
        result.past_count
          ? `Review ${result.extracted_count} extracted events. ${result.past_count} already passed and will not be added unless you include past deadlines.`
          : `Review ${result.extracted_count} extracted events before confirming.`,
      );
    } catch (err) {
      setMessage(formatApiError(err));
    } finally {
      setBusy(false);
    }
  }

  async function confirmPreview(includePast: boolean) {
    if (!userId || !preview) return;
    setBusy(true);
    setMessage(null);
    try {
      const result = await api.confirmDeadlines(userId, preview.document_id, preview.events, includePast, accessToken);
      setMessage(`Confirmed ${result.extracted_count} events. ${!includePast && preview.past_count ? `${preview.past_count} past events were skipped.` : ''}`);
      setPreview(null);
    } catch (err) {
      setMessage(formatApiError(err));
    } finally {
      setBusy(false);
    }
  }

  function updateDraft(tempId: string, patch: Partial<ExtractedEventDraft>) {
    setPreview((current) =>
      current
        ? { ...current, events: current.events.map((event) => (event.temp_id === tempId ? { ...event, ...patch } : event)) }
        : current,
    );
  }

  function removeDraft(tempId: string) {
    setPreview((current) => (current ? { ...current, events: current.events.filter((event) => event.temp_id !== tempId) } : current));
  }

  function handleCourseSelect(value: string) {
    if (value === '__add_course__') {
      onNavigate('courses');
      return;
    }
    setCourseId(value);
  }

  async function deleteDocument(documentId: string, title: string) {
    if (!userId || !window.confirm(`Delete "${title}" and its extracted chunks/events?`)) return;
    setBusy(true);
    setMessage(null);
    try {
      await api.deleteDocument(userId, documentId, accessToken);
      setMessage('Document deleted.');
      await documents.reload();
    } catch (err) {
      setMessage(formatApiError(err));
    } finally {
      setBusy(false);
    }
  }

  if (!userId) return <EmptyState icon={AlertCircle} title="Add your user UUID" body="Paste your Supabase Auth user UUID in the header before uploading PDFs." />;

  return (
    <div className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
      <form onSubmit={handleUpload} className="rounded-lg border border-line bg-white p-5 shadow-soft">
        <h2 className="text-lg font-semibold">Upload PDF</h2>
        <div className="mt-5 space-y-4">
          <label className="block text-sm font-medium text-ink">
            Course
            <select value={courseId} onChange={(event) => handleCourseSelect(event.target.value)} className="mt-2 w-full rounded-lg border border-line bg-white px-3 py-2 text-sm outline-none focus:border-brand">
              <option value="">No course selected</option>
              {courses.data?.map((course) => <option key={course.id} value={course.id}>{course.name}</option>)}
              <option value="__add_course__">+ Add course...</option>
            </select>
          </label>
          <label className="grid min-h-44 cursor-pointer place-items-center rounded-lg border border-dashed border-line bg-app px-4 py-6 text-center hover:border-brand">
            <FileUp className="text-brand" size={28} />
            <span className="mt-3 text-sm font-medium">{file ? file.name : 'Choose a syllabus or lecture PDF'}</span>
            <span className="mt-1 text-xs text-muted">PDF files only</span>
            <input type="file" accept="application/pdf" onChange={(event) => setFile(event.target.files?.[0] ?? null)} className="hidden" />
          </label>
        </div>
        {message && <p className="mt-4 rounded-lg bg-app px-3 py-2 text-sm text-muted">{message}</p>}
        <button disabled={busy || !file} className="mt-5 flex w-full items-center justify-center gap-2 rounded-lg bg-brand px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">
          <FileUp size={17} />
          {busy ? 'Working...' : 'Upload and process'}
        </button>
      </form>

      <section className="rounded-lg border border-line bg-white p-5 shadow-soft">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Documents</h2>
          <button onClick={documents.reload} className="grid h-9 w-9 place-items-center rounded-lg border border-line text-muted hover:text-ink" title="Refresh documents">
            <RefreshCw size={16} />
          </button>
        </div>
        <div className="max-h-[560px] space-y-3 overflow-y-auto pr-1">
          {documents.data?.length ? (
            documents.data.map((doc) => (
              <div key={doc.id} className="rounded-lg border border-line p-4">
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div className="flex gap-3">
                    <div className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-app text-brand"><FileText size={18} /></div>
                    <div>
                      <p className="font-semibold">{doc.title}</p>
                      <p className="mt-1 text-sm text-muted">{doc.file_name} · {(doc.file_size / 1024).toFixed(1)} KB</p>
                      <p className="mt-1 break-all text-xs text-muted">{doc.id}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusPill value={doc.status} />
                    <button disabled={busy || doc.status !== 'processed'} onClick={() => previewExtraction(doc.id)} className="grid h-9 w-9 place-items-center rounded-lg border border-line text-muted hover:text-ink disabled:opacity-40" title="Extract deadlines">
                      <Sparkles size={16} />
                    </button>
                    <button disabled={busy} onClick={() => deleteDocument(doc.id, doc.title)} className="grid h-9 w-9 place-items-center rounded-lg border border-line text-muted hover:border-red-200 hover:bg-red-50 hover:text-red-700 disabled:opacity-40" title="Delete document">
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <EmptyState icon={FileText} title="No PDFs yet" body="Upload a syllabus or lecture PDF to start building your course memory." />
          )}
        </div>
      </section>

      {preview && (
        <section className="xl:col-span-2 rounded-lg border border-line bg-white p-5 shadow-soft">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-lg font-semibold">Review extracted deadlines</h2>
              <p className="mt-1 text-sm text-muted">
                {preview.future_count} upcoming · {preview.past_count} already passed · edit anything that looks wrong before confirming.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button onClick={() => setPreview(null)} className="flex items-center gap-2 rounded-lg border border-line px-3 py-2 text-sm text-muted hover:text-ink"><X size={16} />Cancel</button>
              <button disabled={busy} onClick={() => confirmPreview(false)} className="flex items-center gap-2 rounded-lg bg-brand px-3 py-2 text-sm font-semibold text-white disabled:opacity-50"><Check size={16} />Confirm upcoming only</button>
              {preview.past_count > 0 && <button disabled={busy} onClick={() => confirmPreview(true)} className="flex items-center gap-2 rounded-lg border border-line px-3 py-2 text-sm text-muted hover:text-ink">Include past too</button>}
            </div>
          </div>
          <div className="mt-5 max-h-[620px] overflow-auto pr-1">
            <table className="w-full min-w-[980px] border-separate border-spacing-0 text-left text-sm">
              <thead className="text-muted">
                <tr>
                  <th className="border-b border-line py-3 font-medium">Title</th>
                  <th className="border-b border-line py-3 font-medium">Type</th>
                  <th className="border-b border-line py-3 font-medium">Due at</th>
                  <th className="border-b border-line py-3 font-medium">Weight</th>
                  <th className="border-b border-line py-3 font-medium">Evidence</th>
                  <th className="border-b border-line py-3 font-medium">Status</th>
                  <th className="border-b border-line py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {preview.events.map((event) => (
                  <tr key={event.temp_id}>
                    <td className="border-b border-line py-3 pr-3"><input value={event.title} onChange={(e) => updateDraft(event.temp_id, { title: e.target.value })} className="w-48 rounded-lg border border-line px-2 py-1 outline-none focus:border-brand" /></td>
                    <td className="border-b border-line py-3 pr-3">
                      <select value={event.event_type} onChange={(e) => updateDraft(event.temp_id, { event_type: e.target.value as ExtractedEventDraft['event_type'] })} className="rounded-lg border border-line px-2 py-1 outline-none focus:border-brand">
                        {['assignment', 'quiz', 'exam', 'project', 'reading', 'lecture', 'other'].map((type) => <option key={type} value={type}>{type}</option>)}
                      </select>
                    </td>
                    <td className="border-b border-line py-3 pr-3">
                      <DateTimeDraftEditor event={event} onChange={(dueAt) => updateDraft(event.temp_id, { due_at: dueAt })} />
                    </td>
                    <td className="border-b border-line py-3 pr-3"><input type="number" value={event.grading_weight ?? ''} onChange={(e) => updateDraft(event.temp_id, { grading_weight: e.target.value ? Number(e.target.value) : null })} placeholder={event.grading_weight_text ?? 'N/A'} className="w-24 rounded-lg border border-line px-2 py-1 outline-none focus:border-brand" /></td>
                    <td className="max-w-sm border-b border-line py-3 pr-3 text-xs leading-5 text-muted">{event.evidence || 'No evidence'}</td>
                    <td className="border-b border-line py-3 pr-3"><StatusPill value={event.verification_status} /></td>
                    <td className="border-b border-line py-3 pr-3"><button onClick={() => removeDraft(event.temp_id)} className="grid h-8 w-8 place-items-center rounded-lg border border-line text-muted hover:border-red-200 hover:bg-red-50 hover:text-red-700" title="Remove draft"><Trash2 size={15} /></button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}

function DateTimeDraftEditor({ event, onChange }: { event: ExtractedEventDraft; onChange: (dueAt: string | null) => void }) {
  const parsed = event.due_at ? new Date(event.due_at) : null;
  const dateValue = parsed && !Number.isNaN(parsed.getTime()) ? toDateInputValue(parsed) : '';
  const timeValue = parsed && !Number.isNaN(parsed.getTime()) ? toTimeInputValue(parsed) : '23:59';

  function update(nextDate: string, nextTime: string) {
    if (!nextDate) {
      onChange(null);
      return;
    }
    const normalizedTime = nextTime || '23:59';
    onChange(new Date(`${nextDate}T${normalizedTime}:00`).toISOString());
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        <input
          type="date"
          value={dateValue}
          onChange={(e) => update(e.target.value, timeValue)}
          className="rounded-lg border border-line px-2 py-1 outline-none focus:border-brand"
        />
        <input
          type="time"
          value={timeValue}
          onChange={(e) => update(dateValue, e.target.value)}
          className="rounded-lg border border-line px-2 py-1 outline-none focus:border-brand"
        />
        <button type="button" onClick={() => onChange(null)} className="rounded-lg border border-line px-2 py-1 text-xs text-muted hover:text-ink">
          Clear
        </button>
      </div>
      <p className="text-xs text-muted">Source: {event.due_date_text || 'No date found'}</p>
      {event.is_past && <p className="text-xs text-amber-700">Already passed</p>}
    </div>
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
