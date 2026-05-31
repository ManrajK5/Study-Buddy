from typing import TypedDict
from uuid import UUID

from langgraph.graph import END, StateGraph

from app.database.supabase import get_supabase_admin
from app.models.schemas import DocumentStatus
from app.rag.chunking import DocumentChunker
from app.rag.embeddings import EmbeddingService
from app.utils.pdf import PdfTextExtractor


class AcademicWorkflowState(TypedDict, total=False):
    user_id: UUID
    course_id: UUID | None
    document_id: UUID
    file_bytes: bytes
    file_name: str
    pages: list[dict]
    chunks: list[dict]
    extracted_events: list[dict]
    validated_events: list[dict]


class AcademicWorkflow:
    def __init__(self) -> None:
        graph = StateGraph(AcademicWorkflowState)
        graph.add_node("pdf_extraction_agent", self._extract_pdf)
        graph.add_node("deadline_parsing_agent", self._parse_deadlines)
        graph.add_node("validation_agent", self._validate_events)
        graph.add_node("study_planner_agent", self._prepare_study_plan_context)
        graph.add_edge("pdf_extraction_agent", "deadline_parsing_agent")
        graph.add_edge("deadline_parsing_agent", "validation_agent")
        graph.add_edge("validation_agent", "study_planner_agent")
        graph.add_edge("study_planner_agent", END)
        graph.set_entry_point("pdf_extraction_agent")
        self.graph = graph.compile()

    async def process_uploaded_document(
        self,
        user_id: UUID,
        course_id: UUID | None,
        document_id: UUID,
        file_bytes: bytes,
        file_name: str,
    ) -> None:
        supabase = get_supabase_admin()
        supabase.table("documents").update({"status": DocumentStatus.processing.value}).eq("id", str(document_id)).execute()
        try:
            await self.graph.ainvoke(
                {
                    "user_id": user_id,
                    "course_id": course_id,
                    "document_id": document_id,
                    "file_bytes": file_bytes,
                    "file_name": file_name,
                }
            )
            supabase.table("documents").update({"status": DocumentStatus.processed.value, "extraction_error": None}).eq(
                "id", str(document_id)
            ).execute()
        except Exception as exc:
            supabase.table("documents").update(
                {"status": DocumentStatus.failed.value, "extraction_error": str(exc)}
            ).eq("id", str(document_id)).execute()
            raise

    async def _extract_pdf(self, state: AcademicWorkflowState) -> AcademicWorkflowState:
        pages = await PdfTextExtractor().extract_pages(state["file_bytes"], state["file_name"])
        chunks = DocumentChunker().split_pages(pages)
        embeddings = await EmbeddingService().embed_texts([chunk.content for chunk in chunks])
        records = []
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            records.append(
                {
                    "document_id": str(state["document_id"]),
                    "user_id": str(state["user_id"]),
                    "course_id": str(state["course_id"]) if state.get("course_id") else None,
                    "content": chunk.content,
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                    "metadata": chunk.metadata,
                    "embedding": embedding,
                }
            )
        if records:
            get_supabase_admin().table("document_chunks").insert(records).execute()
        return {**state, "pages": pages, "chunks": records}

    async def _parse_deadlines(self, state: AcademicWorkflowState) -> AcademicWorkflowState:
        # Next implementation slice: call Gemini with structured output against syllabus chunks.
        return {**state, "extracted_events": []}

    async def _validate_events(self, state: AcademicWorkflowState) -> AcademicWorkflowState:
        # Next implementation slice: verify source evidence and assign confidence scores.
        return {**state, "validated_events": state.get("extracted_events", [])}

    async def _prepare_study_plan_context(self, state: AcademicWorkflowState) -> AcademicWorkflowState:
        # Next implementation slice: generate weekly plan candidates after verified events exist.
        return state
