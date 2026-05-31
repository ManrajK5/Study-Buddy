from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.models.schemas import AnalyticsSummary
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
async def analytics_summary(user_id: UUID = Depends(get_current_user_id)) -> AnalyticsSummary:
    return await AnalyticsService().get_summary(user_id=user_id)
