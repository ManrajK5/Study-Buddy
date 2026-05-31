from datetime import datetime, timedelta, timezone
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from postgrest.exceptions import APIError

from app.database.supabase import get_supabase_admin
from app.models.schemas import CalendarSyncFailure, CalendarSyncRequest, CalendarSyncResponse
from app.utils.supabase_errors import raise_supabase_http_error


class GoogleCalendarService:
    async def sync_deadlines(self, user_id: UUID, payload: CalendarSyncRequest) -> CalendarSyncResponse:
        events = self._load_events(user_id=user_id, event_ids=payload.event_ids)
        synced_count = 0
        failed: list[CalendarSyncFailure] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for event in events:
                if not event.get("due_at"):
                    continue
                response = await client.post(
                    f"https://www.googleapis.com/calendar/v3/calendars/{payload.calendar_id}/events",
                    headers={"Authorization": f"Bearer {payload.google_access_token}", "Content-Type": "application/json"},
                    json=self._to_google_event(event),
                )
                if response.status_code in {200, 201}:
                    synced_count += 1
                    continue
                if response.status_code in {401, 403}:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Google Calendar token is missing, expired, or does not include the calendar.events scope. Sign in with Google again and retry.",
                    )
                failed.append(
                    CalendarSyncFailure(
                        event_id=event["id"],
                        title=event["title"],
                        error=response.text[:500],
                    )
                )

        return CalendarSyncResponse(synced_count=synced_count, failed=failed)

    def _load_events(self, user_id: UUID, event_ids: list[UUID] | None) -> list[dict]:
        query = (
            get_supabase_admin()
            .table("academic_events")
            .select("id,title,event_type,description,due_at,grading_weight,estimated_hours,confidence_score,verification_status")
            .eq("user_id", str(user_id))
            .not_.is_("due_at", "null")
            .gte("due_at", datetime.now(timezone.utc).isoformat())
            .order("due_at")
        )
        if event_ids:
            query = query.in_("id", [str(event_id) for event_id in event_ids])
        try:
            response = query.execute()
        except APIError as exc:
            raise_supabase_http_error(exc)
        return response.data

    def _to_google_event(self, event: dict) -> dict:
        start = event["due_at"]
        end = self._end_time(start)
        description = event.get("description") or "Synced from Study Buddy."
        metadata = [
            f"Type: {event.get('event_type')}",
            f"Verification: {event.get('verification_status')}",
        ]
        if event.get("grading_weight") is not None:
            metadata.append(f"Weight: {event['grading_weight']}%")
        if event.get("confidence_score") is not None:
            metadata.append(f"Extraction confidence: {round(event['confidence_score'] * 100)}%")

        return {
            "summary": f"Study Buddy: {event['title']}",
            "description": f"{description}\n\n" + "\n".join(metadata),
            "start": {"dateTime": start},
            "end": {"dateTime": end},
            "reminders": {"useDefault": True},
            "extendedProperties": {"private": {"study_buddy_event_id": str(event["id"])}},
        }

    def _end_time(self, start: str) -> str:
        from datetime import datetime

        normalized = start.replace("Z", "+00:00")
        return (datetime.fromisoformat(normalized) + timedelta(minutes=30)).isoformat()
