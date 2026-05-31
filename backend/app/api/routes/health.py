from fastapi import APIRouter

from app.core.config import settings
from app.rag.embeddings import EmbeddingService

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
        "supabase_configured": settings.is_supabase_configured,
    }


@router.get("/health/embedding")
async def embedding_health_check() -> dict[str, int | list[float] | str]:
    embedding = await EmbeddingService().embed_query("Study Buddy embedding health check")
    return {
        "status": "ok",
        "dimensions": len(embedding),
        "expected_dimensions": settings.embedding_dimensions,
        "preview": embedding[:5],
    }
