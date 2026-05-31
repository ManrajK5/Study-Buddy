from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from postgrest.exceptions import APIError

from app.database.supabase import get_supabase_admin
from app.models.schemas import AcademicEventRead, AcademicEventUpdate
from app.utils.supabase_errors import raise_supabase_http_error


class EventService:
    async def update_event(self, user_id: UUID, event_id: UUID, payload: AcademicEventUpdate) -> AcademicEventRead:
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No event fields provided.")
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        if updates.get("due_at") is not None:
            updates["due_at"] = updates["due_at"].isoformat()
        for key in ("event_type", "verification_status"):
            if updates.get(key) is not None:
                updates[key] = updates[key].value

        try:
            response = (
                get_supabase_admin()
                .table("academic_events")
                .update(updates)
                .eq("id", str(event_id))
                .eq("user_id", str(user_id))
                .execute()
            )
        except APIError as exc:
            raise_supabase_http_error(exc)
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic event not found.")
        return AcademicEventRead.model_validate(response.data[0])

    async def delete_event(self, user_id: UUID, event_id: UUID) -> None:
        try:
            get_supabase_admin().table("academic_events").delete().eq("id", str(event_id)).eq("user_id", str(user_id)).execute()
        except APIError as exc:
            raise_supabase_http_error(exc)
