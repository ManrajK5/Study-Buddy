from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status

from app.api.deps import get_current_user_id
from app.models.schemas import DeadlineExtractionConfirmRequest, DeadlineExtractionPreviewResponse, DeadlineExtractionResponse, DocumentRead
from app.services.deadline_extraction_service import DeadlineExtractionService
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    course_id: UUID | None = Form(default=None),
    user_id: UUID = Depends(get_current_user_id),
) -> DocumentRead:
    return await DocumentService().upload_and_process(user_id=user_id, course_id=course_id, file=file)


@router.get("", response_model=list[DocumentRead])
async def list_documents(user_id: UUID = Depends(get_current_user_id)) -> list[DocumentRead]:
    return await DocumentService().list_documents(user_id=user_id)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: UUID, user_id: UUID = Depends(get_current_user_id)) -> Response:
    await DocumentService().delete_document(user_id=user_id, document_id=document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{document_id}/extract-deadlines", response_model=DeadlineExtractionResponse)
async def extract_document_deadlines(
    document_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
) -> DeadlineExtractionResponse:
    return await DeadlineExtractionService().extract_for_document(user_id=user_id, document_id=document_id)


@router.post("/{document_id}/extract-deadlines/preview", response_model=DeadlineExtractionPreviewResponse)
async def preview_document_deadlines(
    document_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
) -> DeadlineExtractionPreviewResponse:
    return await DeadlineExtractionService().preview_for_document(user_id=user_id, document_id=document_id)


@router.post("/{document_id}/extract-deadlines/confirm", response_model=DeadlineExtractionResponse)
async def confirm_document_deadlines(
    document_id: UUID,
    payload: DeadlineExtractionConfirmRequest,
    user_id: UUID = Depends(get_current_user_id),
) -> DeadlineExtractionResponse:
    return await DeadlineExtractionService().confirm_extraction(user_id=user_id, document_id=document_id, payload=payload)
