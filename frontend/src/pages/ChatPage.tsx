import { AlertCircle, Bot, BookOpen, Send, User } from 'lucide-react';
import { FormEvent, useState } from 'react';
import { EmptyState } from '../components/EmptyState';
import { useAppContext } from '../context/AppContext';
import { useAsync } from '../hooks/useAsync';
import { api, formatApiError } from '../services/api';

type Message = {
  role: 'user' | 'assistant';
  content: string;
  citations?: { page_number?: number | null; snippet: string; similarity: number }[];
};

export function ChatPage() {
  const { userId, accessToken } = useAppContext();
  const courses = useAsync(() => (userId ? api.listCourses(userId, accessToken) : Promise.resolve([])), [userId, accessToken]);
  const [courseId, setCourseId] = useState('');
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function ask(event: FormEvent) {
    event.preventDefault();
    if (!userId || !question.trim()) return;
    const nextQuestion = question.trim();
    setMessages((current) => [...current, { role: 'user', content: nextQuestion }]);
    setQuestion('');
    setLoading(true);
    setError(null);
    try {
      const response = await api.chat(userId, { question: nextQuestion, course_id: courseId || null, session_id: null, top_k: 6 }, accessToken);
      setMessages((current) => [...current, { role: 'assistant', content: response.answer, citations: response.citations }]);
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  }

  if (!userId) return <EmptyState icon={AlertCircle} title="Add your user UUID" body="Paste your Supabase Auth user UUID in the header before chatting with documents." />;

  return (
    <div className="grid min-h-[calc(100vh-140px)] gap-6 xl:grid-cols-[0.75fr_1.25fr]">
      <aside className="rounded-lg border border-line bg-white p-5 shadow-soft">
        <h2 className="text-lg font-semibold">Chat settings</h2>
        <label className="mt-5 block text-sm font-medium text-ink">
          Course scope
          <select value={courseId} onChange={(event) => setCourseId(event.target.value)} className="mt-2 w-full rounded-lg border border-line bg-white px-3 py-2 text-sm outline-none focus:border-brand">
            <option value="">All uploaded documents</option>
            {courses.data?.map((course) => <option key={course.id} value={course.id}>{course.name}</option>)}
          </select>
        </label>
        <div className="mt-6 rounded-lg border border-line bg-app p-4">
          <div className="flex items-center gap-2 text-sm font-medium"><BookOpen size={16} /> Good test questions</div>
          <div className="mt-3 space-y-2 text-sm text-muted">
            {['What is this document about?', 'What assignments are mentioned?', 'How much is the final exam worth?', 'What should I study today?'].map((sample) => (
              <button key={sample} onClick={() => setQuestion(sample)} className="block w-full rounded-lg bg-white px-3 py-2 text-left hover:text-ink">
                {sample}
              </button>
            ))}
          </div>
        </div>
      </aside>

      <section className="flex min-h-[620px] flex-col rounded-lg border border-line bg-white shadow-soft">
        <div className="border-b border-line px-5 py-4">
          <h2 className="text-lg font-semibold">Document chat</h2>
          <p className="text-sm text-muted">Responses are grounded in retrieved document chunks.</p>
        </div>
        <div className="flex-1 space-y-4 overflow-y-auto p-5">
          {messages.length ? (
            messages.map((message, index) => <ChatBubble key={`${message.role}-${index}`} message={message} />)
          ) : (
            <EmptyState icon={Bot} title="Ask your first question" body="Choose a course scope and ask Study Buddy about your uploaded documents." />
          )}
          {loading && <div className="rounded-lg border border-line bg-app px-4 py-3 text-sm text-muted">Thinking through your course context...</div>}
          {error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
        </div>
        <form onSubmit={ask} className="flex gap-3 border-t border-line p-4">
          <input
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask about deadlines, lectures, grading, or study priorities"
            className="min-w-0 flex-1 rounded-lg border border-line px-3 py-2 text-sm outline-none focus:border-brand"
          />
          <button disabled={loading || !question.trim()} className="grid h-10 w-10 place-items-center rounded-lg bg-brand text-white disabled:opacity-50" title="Send message">
            <Send size={18} />
          </button>
        </form>
      </section>
    </div>
  );
}

function ChatBubble({ message }: { message: Message }) {
  const Icon = message.role === 'assistant' ? Bot : User;
  return (
    <div className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
      {message.role === 'assistant' && <Avatar icon={Icon} />}
      <div className={`max-w-[82%] rounded-lg px-4 py-3 ${message.role === 'user' ? 'bg-brand text-white' : 'bg-app text-ink'}`}>
        <p className="whitespace-pre-wrap text-sm leading-6">{message.content}</p>
        {message.citations?.length ? (
          <div className="mt-3 space-y-2 border-t border-line/70 pt-3">
            {message.citations.slice(0, 3).map((citation, index) => (
              <p key={index} className="text-xs leading-5 text-muted">
                Page {citation.page_number ?? 'unknown'} · {(citation.similarity * 100).toFixed(1)}% match · {citation.snippet}
              </p>
            ))}
          </div>
        ) : null}
      </div>
      {message.role === 'user' && <Avatar icon={Icon} />}
    </div>
  );
}

function Avatar({ icon: Icon }: { icon: typeof Bot }) {
  return <div className="grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-line bg-white text-muted"><Icon size={17} /></div>;
}
