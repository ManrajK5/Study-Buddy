from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.api.deps import get_current_user_id
from app.models.schemas import CalendarSyncRequest, CalendarSyncResponse
from app.services.calendar_service import GoogleCalendarService

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/export.ics")
async def export_calendar_ics(user_id: UUID = Depends(get_current_user_id)) -> Response:
    content = await GoogleCalendarService().export_deadlines_ics(user_id=user_id)
    return Response(
        content=content,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="study-buddy-deadlines.ics"'},
    )


@router.post("/sync", response_model=CalendarSyncResponse)
async def sync_google_calendar(
    payload: CalendarSyncRequest,
    user_id: UUID = Depends(get_current_user_id),
) -> CalendarSyncResponse:
    return await GoogleCalendarService().sync_deadlines(user_id=user_id, payload=payload)
