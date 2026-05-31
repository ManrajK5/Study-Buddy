import hashlib
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from postgrest.exceptions import APIError

from app.agents.workflow import AcademicWorkflow
from app.core.config import settings
from app.database.supabase import get_supabase_admin
from app.models.schemas import DocumentRead, DocumentStatus
from app.utils.supabase_errors import raise_supabase_http_error


class DocumentService:
    allowed_mime_types = {"application/pdf"}

    async def upload_and_process(self, user_id: UUID, course_id: UUID | None, file: UploadFile) -> DocumentRead:
        await self._validate_pdf(file)
        document_id = uuid4()
        now = datetime.now(timezone.utc)
        file_bytes = await file.read()
        content_sha256 = hashlib.sha256(file_bytes).hexdigest()
        await self._reject_duplicate(user_id=user_id, course_id=course_id, content_sha256=content_sha256, file_name=file.filename or "upload.pdf")
        storage_path = f"{user_id}/{document_id}/{file.filename}"

        supabase = get_supabase_admin()
        supabase.storage.from_(settings.supabase_storage_bucket).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": file.content_type or "application/pdf"},
        )

        record = {
            "id": str(document_id),
            "user_id": str(user_id),
            "course_id": str(course_id) if course_id else None,
            "title": Path(file.filename or "Untitled PDF").stem,
            "file_path": storage_path,
            "file_name": file.filename or "upload.pdf",
            "mime_type": file.content_type or "application/pdf",
            "file_size": len(file_bytes),
            "content_sha256": content_sha256,
            "status": DocumentStatus.uploaded.value,
            "extraction_error": None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        try:
            supabase.table("documents").insert(record).execute()
        except APIError as exc:
            raise_supabase_http_error(exc)

        # For production, dispatch this workflow to a background worker.
        await AcademicWorkflow().process_uploaded_document(
            user_id=user_id,
            course_id=course_id,
            document_id=document_id,
            file_bytes=file_bytes,
            file_name=file.filename or "upload.pdf",
        )
        return DocumentRead.model_validate({**record, "status": DocumentStatus.processing.value})

    async def list_documents(self, user_id: UUID) -> list[DocumentRead]:
        try:
            response = (
                get_supabase_admin()
                .table("documents")
                .select("*")
                .eq("user_id", str(user_id))
                .order("created_at", desc=True)
                .execute()
            )
        except APIError as exc:
            raise_supabase_http_error(exc)
        return [DocumentRead.model_validate(row) for row in response.data]

    async def delete_document(self, user_id: UUID, document_id: UUID) -> None:
        supabase = get_supabase_admin()
        try:
            response = (
                supabase.table("documents")
                .select("id,file_path")
                .eq("id", str(document_id))
                .eq("user_id", str(user_id))
                .single()
                .execute()
            )
        except APIError as exc:
            raise_supabase_http_error(exc)
        document = response.data
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

        try:
            supabase.storage.from_(settings.supabase_storage_bucket).remove([document["file_path"]])
        except Exception:
            # Keep deleting metadata even if the object was already missing from storage.
            pass

        try:
            supabase.table("documents").delete().eq("id", str(document_id)).eq("user_id", str(user_id)).execute()
        except APIError as exc:
            raise_supabase_http_error(exc)

    async def _validate_pdf(self, file: UploadFile) -> None:
        if file.content_type not in self.allowed_mime_types:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF uploads are supported.")
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file must have a .pdf extension.")
        size = file.size or 0
        if size and size > settings.max_upload_bytes:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="PDF exceeds upload size limit.")

    async def _reject_duplicate(self, user_id: UUID, course_id: UUID | None, content_sha256: str, file_name: str) -> None:
        query = (
            get_supabase_admin()
            .table("documents")
            .select("id,title,file_name,created_at")
            .eq("user_id", str(user_id))
            .eq("content_sha256", content_sha256)
        )
        query = query.eq("course_id", str(course_id)) if course_id else query.is_("course_id", "null")
        try:
            response = query.limit(1).execute()
        except APIError as exc:
            raise_supabase_http_error(exc)
        if response.data:
            existing = response.data[0]
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Duplicate PDF detected. '{file_name}' matches existing document '{existing['file_name']}'.",
            )
