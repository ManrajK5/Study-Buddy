from datetime import datetime, timezone
from uuid import UUID

from app.database.supabase import get_supabase_admin
from app.models.schemas import AcademicEventRead, AnalyticsSummary, WorkloadPoint


class AnalyticsService:
    async def get_summary(self, user_id: UUID) -> AnalyticsSummary:
        response = (
            get_supabase_admin()
            .table("academic_events")
            .select("*,courses(name,code,color)")
            .eq("user_id", str(user_id))
            .gte("due_at", datetime.now(timezone.utc).isoformat())
            .order("due_at")
            .limit(50)
            .execute()
        )
        events = [self._event_from_row(row) for row in response.data]
        assignment_count = sum(event.event_type == "assignment" for event in events)
        exam_count = sum(event.event_type == "exam" for event in events)
        confidence_values = [event.confidence_score for event in events if event.confidence_score is not None]
        average_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else None

        weekly: dict[str, WorkloadPoint] = {}
        for event in events:
            if not event.due_at:
                continue
            week_start = event.due_at.date()
            week_start = week_start.fromordinal(week_start.toordinal() - week_start.weekday())
            key = week_start.isoformat()
            current = weekly.get(key) or WorkloadPoint(week_start=week_start, deadline_count=0, estimated_hours=0)
            current.deadline_count += 1
            current.estimated_hours += event.estimated_hours or 0
            weekly[key] = current

        return AnalyticsSummary(
            upcoming_deadlines=events[:10],
            workload_by_week=list(weekly.values()),
            assignment_count=assignment_count,
            exam_count=exam_count,
            average_confidence=average_confidence,
        )

    def _event_from_row(self, row: dict) -> AcademicEventRead:
        course = row.pop("courses", None) or {}
        return AcademicEventRead.model_validate(
            {
                **row,
                "course_name": course.get("name"),
                "course_code": course.get("code"),
                "course_color": course.get("color"),
            }
        )
