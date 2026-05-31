import { AlertCircle, BookOpen, Plus, Trash2 } from 'lucide-react';
import { FormEvent, useState } from 'react';
import { EmptyState } from '../components/EmptyState';
import { useAppContext } from '../context/AppContext';
import { useAsync } from '../hooks/useAsync';
import { api, formatApiError } from '../services/api';

export function CoursesPage() {
  const { userId, accessToken } = useAppContext();
  const courses = useAsync(() => (userId ? api.listCourses(userId, accessToken) : Promise.resolve([])), [userId, accessToken]);
  const [form, setForm] = useState({ name: '', code: '', term: '', instructor: '', difficulty: 3 });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!userId) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.createCourse(userId, form, accessToken);
      setForm({ name: '', code: '', term: '', instructor: '', difficulty: 3 });
      await courses.reload();
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function deleteCourse(courseId: string, courseName: string) {
    if (!userId) return;
    const confirmed = window.confirm(
      `Delete "${courseName}"? Uploaded PDFs for this course will be kept, but they will no longer be assigned to this course.`,
    );
    if (!confirmed) return;

    setSubmitting(true);
    setError(null);
    try {
      await api.deleteCourse(userId, courseId, accessToken);
      await courses.reload();
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setSubmitting(false);
    }
  }

  if (!userId) return <EmptyState icon={AlertCircle} title="Add your user UUID" body="Paste your Supabase Auth user UUID in the header before managing courses." />;

  return (
    <div className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
      <form onSubmit={handleSubmit} className="rounded-lg border border-line bg-white p-5 shadow-soft">
        <h2 className="text-lg font-semibold">Create course</h2>
        <div className="mt-5 space-y-4">
          <Input label="Course name" value={form.name} onChange={(name) => setForm({ ...form, name })} required />
          <Input label="Code" value={form.code} onChange={(code) => setForm({ ...form, code })} />
          <Input label="Term" value={form.term} onChange={(term) => setForm({ ...form, term })} />
          <Input label="Instructor" value={form.instructor} onChange={(instructor) => setForm({ ...form, instructor })} />
          <label className="block text-sm font-medium text-ink">
            Difficulty
            <input
              type="range"
              min="1"
              max="5"
              value={form.difficulty}
              onChange={(event) => setForm({ ...form, difficulty: Number(event.target.value) })}
              className="mt-2 w-full accent-brand"
            />
            <span className="text-sm text-muted">{form.difficulty}/5</span>
          </label>
        </div>
        {error && <p className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
        <button disabled={submitting || !form.name} className="mt-5 flex w-full items-center justify-center gap-2 rounded-lg bg-brand px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">
          <Plus size={17} />
          {submitting ? 'Creating...' : 'Create course'}
        </button>
      </form>

      <section className="rounded-lg border border-line bg-white p-5 shadow-soft">
        <h2 className="text-lg font-semibold">Courses</h2>
        <div className="mt-5 grid gap-3 md:grid-cols-2">
          {courses.data?.length ? (
            courses.data.map((course) => (
              <div key={course.id} className="rounded-lg border border-line p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="grid h-10 w-10 place-items-center rounded-lg text-white" style={{ backgroundColor: course.color }}>
                      <BookOpen size={18} />
                    </div>
                    <div>
                      <p className="font-semibold">{course.name}</p>
                      <p className="text-sm text-muted">{[course.code, course.term].filter(Boolean).join(' · ') || 'Course'}</p>
                    </div>
                  </div>
                  <button
                    disabled={submitting}
                    onClick={() => deleteCourse(course.id, course.name)}
                    className="grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-line text-muted hover:border-red-200 hover:bg-red-50 hover:text-red-700 disabled:opacity-40"
                    title="Delete course"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
                <p className="mt-3 text-sm text-muted">{course.instructor || 'No instructor set'}</p>
              </div>
            ))
          ) : (
            <div className="md:col-span-2">
              <EmptyState icon={BookOpen} title="No courses yet" body="Create your first course, then attach syllabi and lecture PDFs to it." />
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

function Input({ label, value, onChange, required }: { label: string; value: string; onChange: (value: string) => void; required?: boolean }) {
  return (
    <label className="block text-sm font-medium text-ink">
      {label}
      <input
        required={required}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-2 w-full rounded-lg border border-line bg-white px-3 py-2 text-sm outline-none focus:border-brand"
      />
    </label>
  );
}
