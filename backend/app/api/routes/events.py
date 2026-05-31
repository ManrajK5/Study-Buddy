from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.api.deps import get_current_user_id
from app.models.schemas import AcademicEventRead, AcademicEventUpdate
from app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["events"])


@router.patch("/{event_id}", response_model=AcademicEventRead)
async def update_event(
    event_id: UUID,
    payload: AcademicEventUpdate,
    user_id: UUID = Depends(get_current_user_id),
) -> AcademicEventRead:
    return await EventService().update_event(user_id=user_id, event_id=event_id, payload=payload)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: UUID, user_id: UUID = Depends(get_current_user_id)) -> Response:
    await EventService().delete_event(user_id=user_id, event_id=event_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
