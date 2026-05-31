from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentStatus(StrEnum):
    uploaded = "uploaded"
    processing = "processing"
    processed = "processed"
    failed = "failed"


class AcademicEventType(StrEnum):
    assignment = "assignment"
    quiz = "quiz"
    exam = "exam"
    project = "project"
    reading = "reading"
    lecture = "lecture"
    other = "other"


class VerificationStatus(StrEnum):
    pending = "pending"
    verified = "verified"
    flagged = "flagged"
    rejected = "rejected"


class CourseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    code: str | None = Field(default=None, max_length=32)
    term: str | None = Field(default=None, max_length=64)
    instructor: str | None = Field(default=None, max_length=160)
    color: str = "#2563eb"
    difficulty: int | None = Field(default=None, ge=1, le=5)


class CourseRead(CourseCreate):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime


class DocumentRead(BaseModel):
    id: UUID
    user_id: UUID
    course_id: UUID | None
    title: str
    file_path: str
    file_name: str
    mime_type: str
    file_size: int
    content_sha256: str | None = None
    status: DocumentStatus
    extraction_error: str | None = None
    created_at: datetime
    updated_at: datetime


class AcademicEventRead(BaseModel):
    id: UUID
    course_id: UUID | None
    document_id: UUID | None
    title: str
    event_type: AcademicEventType
    description: str | None = None
    due_at: datetime | None = None
    grading_weight: float | None = None
    estimated_hours: float | None = None
    confidence_score: float | None = None
    verification_status: VerificationStatus
    course_name: str | None = None
    course_code: str | None = None
    course_color: str | None = None


class AcademicEventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    event_type: AcademicEventType | None = None
    description: str | None = None
    due_at: datetime | None = None
    grading_weight: float | None = Field(default=None, ge=0, le=100)
    estimated_hours: float | None = Field(default=None, ge=0, le=200)
    confidence_score: float | None = Field(default=None, ge=0, le=1)
    verification_status: VerificationStatus | None = None


class ExtractedEventDraft(BaseModel):
    temp_id: str
    title: str = Field(min_length=1, max_length=240)
    event_type: AcademicEventType = AcademicEventType.other
    description: str | None = None
    due_at: datetime | None = None
    due_date_text: str | None = None
    grading_weight: float | None = Field(default=None, ge=0, le=100)
    grading_weight_text: str | None = None
    estimated_hours: float | None = Field(default=None, ge=0, le=200)
    confidence_score: float = Field(default=0.5, ge=0, le=1)
    verification_status: VerificationStatus = VerificationStatus.pending
    evidence: str | None = None
    source_chunk_ids: list[UUID] = []
    is_past: bool = False


class DeadlineExtractionPreviewResponse(BaseModel):
    document_id: UUID
    extracted_count: int
    future_count: int
    past_count: int
    events: list[ExtractedEventDraft]


class DeadlineExtractionConfirmRequest(BaseModel):
    events: list[ExtractedEventDraft]
    include_past: bool = False


class DeadlineExtractionResponse(BaseModel):
    document_id: UUID
    extracted_count: int
    events: list[AcademicEventRead]


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    course_id: UUID | None = None
    session_id: UUID | None = None
    top_k: int = Field(default=6, ge=1, le=12)


class Citation(BaseModel):
    document_id: UUID
    chunk_id: UUID
    page_number: int | None = None
    snippet: str
    similarity: float


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = []


class WorkloadPoint(BaseModel):
    week_start: date
    deadline_count: int
    estimated_hours: float


class AnalyticsSummary(BaseModel):
    upcoming_deadlines: list[AcademicEventRead]
    workload_by_week: list[WorkloadPoint]
    assignment_count: int
    exam_count: int
    average_confidence: float | None


class CalendarSyncRequest(BaseModel):
    google_access_token: str = Field(min_length=20)
    calendar_id: str = "primary"
    event_ids: list[UUID] | None = None


class CalendarSyncFailure(BaseModel):
    event_id: UUID
    title: str
    error: str


class CalendarSyncResponse(BaseModel):
    synced_count: int
    failed: list[CalendarSyncFailure] = []
