import json
import re
from datetime import datetime, timezone
from uuid import UUID

from dateutil import parser as date_parser
from fastapi import HTTPException, status
from langchain_google_genai import ChatGoogleGenerativeAI
from postgrest.exceptions import APIError
from pydantic import BaseModel, Field, ValidationError

from app.core.config import settings
from app.database.supabase import get_supabase_admin
from app.models.schemas import (
    AcademicEventRead,
    DeadlineExtractionConfirmRequest,
    DeadlineExtractionPreviewResponse,
    DeadlineExtractionResponse,
    ExtractedEventDraft,
)
from app.utils.supabase_errors import raise_supabase_http_error


class ExtractedDeadline(BaseModel):
    title: str = Field(min_length=1)
    event_type: str = "other"
    description: str | None = None
    due_at: str | None = None
    grading_weight: float | None = None
    estimated_hours: float | None = None
    confidence_score: float = Field(default=0.5, ge=0, le=1)
    verification_status: str = "pending"
    source_chunk_indexes: list[int] = []
    evidence: str | None = None
    due_date_text: str | None = None
    grading_weight_text: str | None = None


class ExtractedDeadlinePayload(BaseModel):
    events: list[ExtractedDeadline] = []


class DeadlineExtractionService:
    async def extract_for_document(self, user_id: UUID, document_id: UUID) -> DeadlineExtractionResponse:
        preview = await self.preview_for_document(user_id=user_id, document_id=document_id)
        return await self.confirm_extraction(
            user_id=user_id,
            document_id=document_id,
            payload=DeadlineExtractionConfirmRequest(events=preview.events, include_past=False),
        )

    async def preview_for_document(self, user_id: UUID, document_id: UUID) -> DeadlineExtractionPreviewResponse:
        if not settings.google_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GOOGLE_API_KEY is required for deadline extraction.",
            )

        supabase = get_supabase_admin()
        try:
            document_response = (
                supabase.table("documents")
                .select("id,user_id,course_id,title,courses(term)")
                .eq("id", str(document_id))
                .eq("user_id", str(user_id))
                .single()
                .execute()
            )
        except APIError as exc:
            raise_supabase_http_error(exc)
        document = document_response.data
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

        try:
            chunks_response = (
                supabase.table("document_chunks")
                .select("id,content,page_number,chunk_index")
                .eq("document_id", str(document_id))
                .eq("user_id", str(user_id))
                .order("chunk_index")
                .execute()
            )
        except APIError as exc:
            raise_supabase_http_error(exc)
        chunks = chunks_response.data
        if not chunks:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document has no processed chunks yet.")

        candidate_chunks = self._select_candidate_chunks(chunks)
        payload = await self._extract_with_gemini(document=document, chunks=candidate_chunks)
        events = [self._to_draft(document, event, chunks, index) for index, event in enumerate(payload.events)]
        return DeadlineExtractionPreviewResponse(
            document_id=document_id,
            extracted_count=len(events),
            future_count=sum(not event.is_past for event in events),
            past_count=sum(event.is_past for event in events),
            events=events,
        )

    async def confirm_extraction(
        self,
        user_id: UUID,
        document_id: UUID,
        payload: DeadlineExtractionConfirmRequest,
    ) -> DeadlineExtractionResponse:
        supabase = get_supabase_admin()
        try:
            document_response = (
                supabase.table("documents")
                .select("id,user_id,course_id,title")
                .eq("id", str(document_id))
                .eq("user_id", str(user_id))
                .single()
                .execute()
            )
        except APIError as exc:
            raise_supabase_http_error(exc)
        document = document_response.data
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

        selected_events = [event for event in payload.events if payload.include_past or not event.is_past]
        records = [self._draft_to_record(user_id, document, event) for event in selected_events]
        try:
            supabase.table("academic_events").delete().eq("document_id", str(document_id)).eq("user_id", str(user_id)).execute()
        except APIError as exc:
            raise_supabase_http_error(exc)
        if not records:
            return DeadlineExtractionResponse(document_id=document_id, extracted_count=0, events=[])

        try:
            insert_response = supabase.table("academic_events").insert(records).execute()
        except APIError as exc:
            raise_supabase_http_error(exc)
        events = [AcademicEventRead.model_validate(row) for row in insert_response.data]
        return DeadlineExtractionResponse(document_id=document_id, extracted_count=len(events), events=events)

    async def _extract_with_gemini(self, document: dict, chunks: list[dict]) -> ExtractedDeadlinePayload:
        context = "\n\n".join(
            f"[chunk_index={chunk['chunk_index']} page={chunk.get('page_number')}]\n{chunk['content']}" for chunk in chunks
        )
        course_term = (document.get("courses") or {}).get("term")
        prompt = f"""
You are Study Buddy's evidence-first syllabus extraction system. Accuracy matters more than quantity.

Extract only real graded academic events from the course document: assignments, quizzes, exams, projects, labs, midterms, final exams, presentations, and required graded checkpoints.

Do not extract generic lecture topics, office hours, textbook readings, policy sections, grading categories without a concrete deliverable, or calendar dates that are not student deadlines/events.

Return only valid JSON in this exact shape:
{{
  "events": [
    {{
      "title": "string",
      "event_type": "assignment|quiz|exam|project|reading|lecture|other",
      "description": "string or null",
      "due_at": "ISO-8601 datetime or null",
      "grading_weight": 25.0,
      "estimated_hours": 3.0,
      "confidence_score": 0.0,
      "verification_status": "verified|pending|flagged",
      "source_chunk_indexes": [0],
      "evidence": "short exact evidence containing the title/date/weight when available",
      "due_date_text": "raw date text from the document or null",
      "grading_weight_text": "raw weight text from the document or null"
    }}
  ]
}}

Rules:
- Every event must have source evidence. If there is no source evidence, omit it.
- For event_type, use the title and evidence. Midterm/final/test = exam. Homework/problem set/essay/report/submission = assignment. Presentation/design capstone = project unless the document calls it an assignment.
- grading_weight must be the percent value for that specific event only. If the document says "Assignments 30%" but lists Assignment 1/2/3 without individual weights, set grading_weight to null and put "Assignments category is 30%" in description.
- grading_weight_text must be the exact raw text that justifies the specific weight. If no exact text justifies it, set grading_weight and grading_weight_text to null.
- due_date_text must be the exact raw date text from the document. due_at should be ISO-8601 if you can confidently normalize it; otherwise set due_at null and keep due_date_text.
- If only a date is given, use 23:59:00 local course time. If only a month/day is given and the course term gives a year, infer that year.
- Use null for unknown due dates or weights. Never guess dates from lecture numbers.
- If a date/weight/type is ambiguous, set verification_status to flagged and confidence_score below 0.7.
- confidence_score >= 0.85 only when title, type, and date or weight are explicitly supported by evidence.
- Do not invent deadlines.
- Merge duplicate mentions of the same event.

Document title: {document["title"]}
Course term: {course_term or "unknown"}

Context:
{context}
"""
        llm = ChatGoogleGenerativeAI(model=settings.gemini_model, google_api_key=settings.google_api_key, temperature=0.1)
        result = await llm.ainvoke(prompt)
        raw = self._strip_json_fences(str(result.content))
        try:
            return ExtractedDeadlinePayload.model_validate_json(raw)
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"message": "Gemini returned invalid deadline JSON.", "raw": raw[:1000]},
            ) from exc

    def _to_draft(self, document: dict, event: ExtractedDeadline, chunks: list[dict], index: int) -> ExtractedEventDraft:
        source_chunk_ids = [
            chunk["id"] for chunk in chunks if chunk["chunk_index"] in set(event.source_chunk_indexes)
        ]
        course_term = (document.get("courses") or {}).get("term")
        parsed_due_at = self._parse_due_at(event.due_at or event.due_date_text, course_term=course_term)
        normalized_type = self._normalize_event_type(event)
        confidence = self._normalized_confidence(event, parsed_due_at)
        verification_status = self._normalized_status(event, parsed_due_at, confidence)
        grading_weight = self._normalized_weight(event)
        due_at_dt = datetime.fromisoformat(parsed_due_at) if parsed_due_at else None
        is_past = bool(due_at_dt and due_at_dt.astimezone(timezone.utc) < datetime.now(timezone.utc))
        return ExtractedEventDraft(
            temp_id=f"draft-{index}",
            title=event.title,
            event_type=normalized_type,
            description=event.description or event.evidence,
            due_at=due_at_dt,
            due_date_text=event.due_date_text,
            grading_weight=grading_weight,
            grading_weight_text=event.grading_weight_text,
            estimated_hours=event.estimated_hours,
            confidence_score=confidence,
            verification_status=verification_status,
            evidence=event.evidence,
            source_chunk_ids=source_chunk_ids,
            is_past=is_past,
        )

    def _draft_to_record(self, user_id: UUID, document: dict, event: ExtractedEventDraft) -> dict:
        return {
            "user_id": str(user_id),
            "course_id": document.get("course_id"),
            "document_id": document["id"],
            "title": event.title,
            "event_type": event.event_type.value,
            "description": event.description or event.evidence,
            "due_at": event.due_at.isoformat() if event.due_at else None,
            "grading_weight": event.grading_weight,
            "estimated_hours": event.estimated_hours,
            "confidence_score": event.confidence_score,
            "verification_status": event.verification_status.value,
            "source_chunk_ids": [str(chunk_id) for chunk_id in event.source_chunk_ids],
            "raw_extraction": event.model_dump(mode="json"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _parse_due_at(self, due_at: str | None, course_term: str | None = None) -> str | None:
        if not due_at:
            return None
        text = due_at.strip()
        year = self._infer_year(course_term) or datetime.now().year
        default = datetime(year=year, month=12, day=31, hour=23, minute=59)
        try:
            parsed = date_parser.parse(text, fuzzy=True, default=default)
            if not re.search(r"\b\d{1,2}:\d{2}\b|\b(am|pm)\b", text, re.I):
                parsed = parsed.replace(hour=23, minute=59, second=0, microsecond=0)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.isoformat()
        except (ValueError, OverflowError, TypeError):
            return None

    def _select_candidate_chunks(self, chunks: list[dict]) -> list[dict]:
        keywords = re.compile(
            r"\b(due|deadline|exam|midterm|final|quiz|assignment|homework|project|paper|essay|report|presentation|"
            r"deliverable|submission|submit|grade|grading|weight|percent|%|schedule|calendar|week)\b",
            re.IGNORECASE,
        )
        scored: list[tuple[int, dict]] = []
        for chunk in chunks:
            content = chunk.get("content") or ""
            score = len(keywords.findall(content))
            if "%" in content:
                score += 2
            if re.search(r"\b\d{1,2}[/-]\d{1,2}\b|\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)", content, re.I):
                score += 2
            scored.append((score, chunk))

        first_chunks = chunks[:6]
        relevant = [chunk for score, chunk in sorted(scored, key=lambda item: item[0], reverse=True) if score > 0][:54]
        selected: dict[int, dict] = {chunk["chunk_index"]: chunk for chunk in first_chunks + relevant}
        return [selected[index] for index in sorted(selected)]

    def _normalize_event_type(self, event: ExtractedDeadline) -> str:
        text = f"{event.title} {event.description or ''} {event.evidence or ''}".lower()
        if re.search(r"\b(final|midterm|exam|test)\b", text):
            return "exam"
        if re.search(r"\b(quiz|quizzes)\b", text):
            return "quiz"
        if re.search(r"\b(project|presentation|capstone|demo)\b", text):
            return "project"
        if re.search(r"\b(homework|assignment|problem set|essay|paper|report|submission|lab)\b", text):
            return "assignment"
        if event.event_type in self._event_types():
            return event.event_type
        return "other"

    def _normalized_weight(self, event: ExtractedDeadline) -> float | None:
        weight = event.grading_weight
        if weight is None or weight < 0 or weight > 100:
            return None
        proof = f"{event.grading_weight_text or ''} {event.evidence or ''}".lower()
        if "%" not in proof and "percent" not in proof:
            return None
        title_words = [word for word in re.findall(r"[a-z0-9]+", event.title.lower()) if len(word) > 2]
        category_only = re.search(r"\b(assignments|quizzes|exams|projects|homework|participation|labs)\b\s*[:\-]?\s*\d+(\.\d+)?\s*%", proof)
        title_supported = any(word in proof for word in title_words[:4])
        if category_only and not title_supported:
            return None
        return round(weight, 2)

    def _normalized_confidence(self, event: ExtractedDeadline, parsed_due_at: str | None) -> float:
        confidence = event.confidence_score
        if not event.evidence:
            confidence = min(confidence, 0.45)
        if event.due_at and not parsed_due_at:
            confidence = min(confidence, 0.55)
        if event.grading_weight is not None and self._normalized_weight(event) is None:
            confidence = min(confidence, 0.55)
        if not parsed_due_at and event.grading_weight is None:
            confidence = min(confidence, 0.65)
        return round(max(0, min(confidence, 1)), 3)

    def _normalized_status(self, event: ExtractedDeadline, parsed_due_at: str | None, confidence: float) -> str:
        if event.verification_status == "rejected":
            return "rejected"
        if confidence >= 0.85 and event.evidence and (parsed_due_at or event.grading_weight is not None):
            return "verified"
        if confidence < 0.7 or (event.due_at and not parsed_due_at):
            return "flagged"
        return "pending"

    def _infer_year(self, course_term: str | None) -> int | None:
        if not course_term:
            return None
        match = re.search(r"\b(20\d{2})\b", course_term)
        return int(match.group(1)) if match else None

    def _strip_json_fences(self, value: str) -> str:
        stripped = value.strip()
        if stripped.startswith("```"):
            stripped = stripped.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        json.loads(stripped)
        return stripped

    def _event_types(self) -> set[str]:
        return {"assignment", "quiz", "exam", "project", "reading", "lecture", "other"}

    def _statuses(self) -> set[str]:
        return {"pending", "verified", "flagged", "rejected"}
