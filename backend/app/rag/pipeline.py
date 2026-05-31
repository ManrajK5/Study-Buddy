from uuid import UUID

from langchain_google_genai import ChatGoogleGenerativeAI
from postgrest.exceptions import APIError

from app.core.config import settings
from app.database.supabase import get_supabase_admin
from app.models.schemas import ChatRequest, ChatResponse, Citation
from app.rag.retriever import SupabaseRetriever
from app.utils.supabase_errors import raise_supabase_http_error


class RagPipeline:
    async def answer_question(self, user_id: UUID, payload: ChatRequest) -> ChatResponse:
        chunks = await SupabaseRetriever().retrieve(
            user_id=user_id,
            question=payload.question,
            course_id=payload.course_id,
            top_k=max(payload.top_k, 8),
        )
        events = self._load_academic_events(user_id=user_id, course_id=payload.course_id)
        documents = self._load_documents(user_id=user_id, course_id=payload.course_id)
        context = "\n\n".join(
            f"[PDF Source {index + 1}, page {chunk.get('page_number')}, similarity={chunk.get('similarity', 0):.3f}]\n{chunk['content']}"
            for index, chunk in enumerate(chunks)
        )
        event_context = "\n".join(
            " | ".join(
                [
                    f"title={event.get('title')}",
                    f"type={event.get('event_type')}",
                    f"due={event.get('due_at') or 'unknown'}",
                    f"weight={event.get('grading_weight') if event.get('grading_weight') is not None else 'unknown'}",
                    f"status={event.get('verification_status')}",
                    f"confidence={event.get('confidence_score')}",
                    f"description={event.get('description') or ''}",
                ]
            )
            for event in events
        )
        document_context = "\n".join(
            f"document={doc.get('title')} | filename={doc.get('file_name')} | status={doc.get('status')} | created={doc.get('created_at')}"
            for doc in documents
        )
        prompt = (
            "You are Study Buddy, a practical academic assistant for a student. Use the structured deadlines first when the "
            "question is about due dates, workload, weights, exams, assignments, or what to study. Use retrieved PDF context "
            "for explanations, policies, lecture content, and evidence.\n\n"
            "Formatting rules:\n"
            "- Do not use emoji.\n"
            "- Do not use horizontal rules.\n"
            "- Do not start with a generic sentence like 'Here is your personalized study plan'.\n"
            "- Keep the answer compact: usually 3-6 bullets or a small markdown table.\n"
            "- Use clean headings only when helpful, such as 'Next Deadlines' or 'Study Plan'.\n"
            "- Dates should be human-readable, for example 'Jun 5, 2026, 8:40 AM'.\n"
            "- For quizzes/exams, include weight only when available and avoid repeating '(Bonus)' unless the source says it.\n"
            "- End with one short next action if useful.\n\n"
            "Answer style:\n"
            "- Be specific and useful, not generic.\n"
            "- If deadlines are relevant, organize by date and clearly mark unknown dates.\n"
            "- If asked what to study, propose a short prioritized plan based on upcoming deadlines and document content.\n"
            "- Mention uncertainty when confidence is low or data is missing.\n"
            "- Ground claims in the supplied context; do not invent course facts.\n"
            "- If the context is insufficient, say exactly what is missing and what PDF/action would help.\n\n"
            f"Uploaded documents:\n{document_context or 'No uploaded document metadata available.'}\n\n"
            f"Structured extracted events/deadlines:\n{event_context or 'No extracted events available.'}\n\n"
            f"Retrieved PDF context:\n{context or 'No relevant PDF chunks were retrieved.'}\n\n"
            f"Student question: {payload.question}"
        )
        llm = ChatGoogleGenerativeAI(model=settings.gemini_model, google_api_key=settings.google_api_key, temperature=0.2)
        result = await llm.ainvoke(prompt)
        citations = [
            Citation(
                document_id=chunk["document_id"],
                chunk_id=chunk["id"],
                page_number=chunk.get("page_number"),
                snippet=chunk["content"][:280],
                similarity=chunk.get("similarity", 0),
            )
            for chunk in chunks
        ]
        return ChatResponse(answer=result.content, citations=citations)

    def _load_academic_events(self, user_id: UUID, course_id: UUID | None) -> list[dict]:
        query = (
            get_supabase_admin()
            .table("academic_events")
            .select("id,title,event_type,description,due_at,grading_weight,estimated_hours,confidence_score,verification_status")
            .eq("user_id", str(user_id))
            .order("due_at", desc=False, nullsfirst=False)
            .limit(40)
        )
        if course_id:
            query = query.eq("course_id", str(course_id))
        try:
            return query.execute().data
        except APIError as exc:
            raise_supabase_http_error(exc)

    def _load_documents(self, user_id: UUID, course_id: UUID | None) -> list[dict]:
        query = (
            get_supabase_admin()
            .table("documents")
            .select("id,title,file_name,status,created_at")
            .eq("user_id", str(user_id))
            .order("created_at", desc=True)
            .limit(20)
        )
        if course_id:
            query = query.eq("course_id", str(course_id))
        try:
            return query.execute().data
        except APIError as exc:
            raise_supabase_http_error(exc)
