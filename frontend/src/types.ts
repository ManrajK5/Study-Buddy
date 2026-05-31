export type Course = {
  id: string;
  user_id: string;
  name: string;
  code?: string | null;
  term?: string | null;
  instructor?: string | null;
  color: string;
  difficulty?: number | null;
  created_at: string;
  updated_at: string;
};

export type DocumentRecord = {
  id: string;
  user_id: string;
  course_id?: string | null;
  title: string;
  file_path: string;
  file_name: string;
  mime_type: string;
  file_size: number;
  content_sha256?: string | null;
  status: 'uploaded' | 'processing' | 'processed' | 'failed';
  extraction_error?: string | null;
  created_at: string;
  updated_at: string;
};

export type AcademicEvent = {
  id: string;
  course_id?: string | null;
  document_id?: string | null;
  title: string;
  event_type: 'assignment' | 'quiz' | 'exam' | 'project' | 'reading' | 'lecture' | 'other';
  description?: string | null;
  due_at?: string | null;
  grading_weight?: number | null;
  estimated_hours?: number | null;
  confidence_score?: number | null;
  verification_status: 'pending' | 'verified' | 'flagged' | 'rejected';
  course_name?: string | null;
  course_code?: string | null;
  course_color?: string | null;
};

export type ExtractedEventDraft = {
  temp_id: string;
  title: string;
  event_type: AcademicEvent['event_type'];
  description?: string | null;
  due_at?: string | null;
  due_date_text?: string | null;
  grading_weight?: number | null;
  grading_weight_text?: string | null;
  estimated_hours?: number | null;
  confidence_score: number;
  verification_status: AcademicEvent['verification_status'];
  evidence?: string | null;
  source_chunk_ids: string[];
  is_past: boolean;
};

export type DeadlinePreview = {
  document_id: string;
  extracted_count: number;
  future_count: number;
  past_count: number;
  events: ExtractedEventDraft[];
};

export type AnalyticsSummary = {
  upcoming_deadlines: AcademicEvent[];
  workload_by_week: { week_start: string; deadline_count: number; estimated_hours: number }[];
  assignment_count: number;
  exam_count: number;
  average_confidence?: number | null;
};

export type ChatResponse = {
  answer: string;
  citations: {
    document_id: string;
    chunk_id: string;
    page_number?: number | null;
    snippet: string;
    similarity: number;
  }[];
};
