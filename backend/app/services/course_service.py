from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from postgrest.exceptions import APIError

from app.database.supabase import get_supabase_admin
from app.models.schemas import CourseCreate, CourseRead
from app.utils.supabase_errors import raise_supabase_http_error


class CourseService:
    async def create_course(self, user_id: UUID, payload: CourseCreate) -> CourseRead:
        now = datetime.now(timezone.utc)
        record = {
            "id": str(uuid4()),
            "user_id": str(user_id),
            "name": payload.name,
            "code": payload.code,
            "term": payload.term,
            "instructor": payload.instructor,
            "color": payload.color,
            "difficulty": payload.difficulty,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        try:
            response = get_supabase_admin().table("courses").insert(record).execute()
        except APIError as exc:
            raise_supabase_http_error(exc)
        return CourseRead.model_validate(response.data[0])

    async def list_courses(self, user_id: UUID) -> list[CourseRead]:
        try:
            response = (
                get_supabase_admin()
                .table("courses")
                .select("*")
                .eq("user_id", str(user_id))
                .order("created_at")
                .execute()
            )
        except APIError as exc:
            raise_supabase_http_error(exc)
        return [CourseRead.model_validate(row) for row in response.data]

    async def delete_course(self, user_id: UUID, course_id: UUID) -> None:
        try:
            response = (
                get_supabase_admin()
                .table("courses")
                .delete()
                .eq("id", str(course_id))
                .eq("user_id", str(user_id))
                .execute()
            )
        except APIError as exc:
            raise_supabase_http_error(exc)
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")
