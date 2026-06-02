from datetime import datetime, timedelta, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

import httpx
from fastapi import HTTPException, status
from postgrest.exceptions import APIError

from app.database.supabase import get_supabase_admin
from app.models.schemas import CalendarSyncFailure, CalendarSyncRequest, CalendarSyncResponse
from app.utils.supabase_errors import raise_supabase_http_error


class GoogleCalendarService:
    async def export_deadlines_ics(self, user_id: UUID, event_ids: list[UUID] | None = None) -> str:
        events = self._load_events(user_id=user_id, event_ids=event_ids)
        timestamp = self._format_ics_datetime(datetime.now(timezone.utc))
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Study Buddy//Academic Deadlines//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Study Buddy Deadlines",
            "X-WR-TIMEZONE:UTC",
        ]

        for event in events:
            if not event.get("due_at"):
                continue
            start = self._parse_datetime(event["due_at"])
            end = start + timedelta(minutes=30)
            description = event.get("description") or "Exported from Study Buddy."
            metadata = [
                f"Type: {event.get('event_type')}",
                f"Verification: {event.get('verification_status')}",
            ]
            if event.get("grading_weight") is not None:
                metadata.append(f"Weight: {event['grading_weight']}%")
            if event.get("estimated_hours") is not None:
                metadata.append(f"Estimated study hours: {event['estimated_hours']}")

            lines.extend(
                [
                    "BEGIN:VEVENT",
                    f"UID:study-buddy-{event['id']}@study-buddy",
                    f"DTSTAMP:{timestamp}",
                    f"DTSTART:{self._format_ics_datetime(start)}",
                    f"DTEND:{self._format_ics_datetime(end)}",
                    f"SUMMARY:{self._escape_ics_text('Study Buddy: ' + event['title'])}",
                    f"DESCRIPTION:{self._escape_ics_text(description + chr(10) + chr(10) + chr(10).join(metadata))}",
                    "BEGIN:VALARM",
                    "TRIGGER:-PT24H",
                    "ACTION:DISPLAY",
                    f"DESCRIPTION:{self._escape_ics_text('Reminder: ' + event['title'])}",
                    "END:VALARM",
                    "END:VEVENT",
                ]
            )

        lines.append("END:VCALENDAR")
        return "\r\n".join(self._fold_ics_line(line) for line in lines) + "\r\n"

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
        normalized = start.replace("Z", "+00:00")
        return (datetime.fromisoformat(normalized) + timedelta(minutes=30)).isoformat()

    def _parse_datetime(self, value: str) -> datetime:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _format_ics_datetime(self, value: datetime) -> str:
        return value.astimezone(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")

    def _escape_ics_text(self, value: str) -> str:
        return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

    def _fold_ics_line(self, line: str) -> str:
        if len(line) <= 75:
            return line
        chunks = [line[:75]]
        remaining = line[75:]
        while remaining:
            chunks.append(" " + remaining[:74])
            remaining = remaining[74:]
        return "\r\n".join(chunks)
