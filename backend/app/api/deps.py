from uuid import UUID

from fastapi import Header, HTTPException, status

from app.core.config import settings
from app.database.supabase import get_supabase_admin


async def get_current_user_id(
    authorization: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
) -> UUID:
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.removeprefix("Bearer ").removeprefix("bearer ").strip()
        try:
            user_response = get_supabase_admin().auth.get_user(token)
            return UUID(user_response.user.id)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Supabase access token.") from exc

    if settings.app_env.lower() == "production":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Supabase Bearer token.",
        )

    # Development fallback for local Swagger/API testing only.
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Supabase Bearer token or X-User-Id development header.",
        )
    try:
        return UUID(x_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid X-User-Id UUID.") from exc
