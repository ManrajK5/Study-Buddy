from fastapi import HTTPException, status
from postgrest.exceptions import APIError


def raise_supabase_http_error(exc: APIError) -> None:
    message = getattr(exc, "message", None) or str(exc)
    details = getattr(exc, "details", None)
    hint = getattr(exc, "hint", None)
    code = getattr(exc, "code", None)

    if "violates foreign key constraint" in message and "user_id" in message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The supplied user id does not exist in Supabase Auth. "
                "Create/sign in a user first, then use that user's auth.users id as X-User-Id."
            ),
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={
            "message": message,
            "details": details,
            "hint": hint,
            "code": code,
        },
    ) from exc
