from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.api.deps import get_current_user_id
from app.models.schemas import CourseCreate, CourseRead
from app.services.course_service import CourseService

router = APIRouter(prefix="/courses", tags=["courses"])


@router.post("", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
async def create_course(payload: CourseCreate, user_id: UUID = Depends(get_current_user_id)) -> CourseRead:
    return await CourseService().create_course(user_id=user_id, payload=payload)


@router.get("", response_model=list[CourseRead])
async def list_courses(user_id: UUID = Depends(get_current_user_id)) -> list[CourseRead]:
    return await CourseService().list_courses(user_id=user_id)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(course_id: UUID, user_id: UUID = Depends(get_current_user_id)) -> Response:
    await CourseService().delete_course(user_id=user_id, course_id=course_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
