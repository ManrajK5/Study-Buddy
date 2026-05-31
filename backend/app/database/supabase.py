from functools import lru_cache

from fastapi import HTTPException, status
from supabase import Client, create_client

from app.core.config import settings


@lru_cache
def get_supabase_admin() -> Client:
    if not settings.is_supabase_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase is not configured. Add SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY to .env.",
        )
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
