from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.models.schemas import CalendarSyncRequest, CalendarSyncResponse
from app.services.calendar_service import GoogleCalendarService

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.post("/sync", response_model=CalendarSyncResponse)
async def sync_google_calendar(
    payload: CalendarSyncRequest,
    user_id: UUID = Depends(get_current_user_id),
) -> CalendarSyncResponse:
    return await GoogleCalendarService().sync_deadlines(user_id=user_id, payload=payload)
