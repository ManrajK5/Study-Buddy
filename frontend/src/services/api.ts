import type { AnalyticsSummary, ChatResponse, Course, DeadlinePreview, DocumentRecord, ExtractedEventDraft } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api/v1';

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
  }
}

type RequestOptions = RequestInit & { userId: string; accessToken?: string | null };

async function request<T>(path: string, options: RequestOptions): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.accessToken) {
    headers.set('Authorization', `Bearer ${options.accessToken}`);
  } else {
    headers.set('x-user-id', options.userId);
  }
  if (!(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  if (!response.ok) {
    const text = await response.text();
    throw new ApiError(text || response.statusText, response.status);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const api = {
  listCourses: (userId: string, accessToken?: string | null) => request<Course[]>('/courses', { method: 'GET', userId, accessToken }),
  createCourse: (userId: string, payload: Partial<Course>, accessToken?: string | null) =>
    request<Course>('/courses', { method: 'POST', userId, accessToken, body: JSON.stringify(payload) }),
  deleteCourse: (userId: string, courseId: string, accessToken?: string | null) =>
    request<void>(`/courses/${courseId}`, { method: 'DELETE', userId, accessToken }),
  listDocuments: (userId: string, accessToken?: string | null) => request<DocumentRecord[]>('/documents', { method: 'GET', userId, accessToken }),
  deleteDocument: (userId: string, documentId: string, accessToken?: string | null) =>
    request<void>(`/documents/${documentId}`, { method: 'DELETE', userId, accessToken }),
  uploadDocument: (userId: string, courseId: string | null, file: File, accessToken?: string | null) => {
    const form = new FormData();
    form.append('file', file);
    if (courseId) form.append('course_id', courseId);
    return request<DocumentRecord>('/documents/upload', { method: 'POST', userId, accessToken, body: form });
  },
  extractDeadlines: (userId: string, documentId: string, accessToken?: string | null) =>
    request<{ document_id: string; extracted_count: number; events: unknown[] }>(`/documents/${documentId}/extract-deadlines`, {
      method: 'POST',
      userId,
      accessToken,
    }),
  previewDeadlines: (userId: string, documentId: string, accessToken?: string | null) =>
    request<DeadlinePreview>(`/documents/${documentId}/extract-deadlines/preview`, { method: 'POST', userId, accessToken }),
  confirmDeadlines: (userId: string, documentId: string, events: ExtractedEventDraft[], includePast: boolean, accessToken?: string | null) =>
    request<{ document_id: string; extracted_count: number; events: unknown[] }>(`/documents/${documentId}/extract-deadlines/confirm`, {
      method: 'POST',
      userId,
      accessToken,
      body: JSON.stringify({ events, include_past: includePast }),
    }),
  chat: (userId: string, payload: { question: string; course_id?: string | null; session_id?: string | null; top_k: number }, accessToken?: string | null) =>
    request<ChatResponse>('/chat', { method: 'POST', userId, accessToken, body: JSON.stringify(payload) }),
  analytics: (userId: string, accessToken?: string | null) => request<AnalyticsSummary>('/analytics/summary', { method: 'GET', userId, accessToken }),
  syncCalendar: (userId: string, googleAccessToken: string, eventIds: string[], accessToken?: string | null) =>
    request<{ synced_count: number; failed: { event_id: string; title: string; error: string }[] }>('/calendar/sync', {
      method: 'POST',
      userId,
      accessToken,
      body: JSON.stringify({ google_access_token: googleAccessToken, calendar_id: 'primary', event_ids: eventIds }),
    }),
  updateEvent: (userId: string, eventId: string, payload: Record<string, unknown>, accessToken?: string | null) =>
    request('/events/' + eventId, { method: 'PATCH', userId, accessToken, body: JSON.stringify(payload) }),
  deleteEvent: (userId: string, eventId: string, accessToken?: string | null) =>
    request<void>('/events/' + eventId, { method: 'DELETE', userId, accessToken }),
};

export function formatApiError(error: unknown): string {
  if (error instanceof ApiError) {
    try {
      const parsed = JSON.parse(error.message);
      return typeof parsed.detail === 'string' ? parsed.detail : JSON.stringify(parsed.detail ?? parsed);
    } catch {
      return `${error.status}: ${error.message}`;
    }
  }
  return error instanceof Error ? error.message : 'Something went wrong.';
}
