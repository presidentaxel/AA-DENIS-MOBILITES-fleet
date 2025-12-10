from datetime import timedelta

from fastapi import HTTPException, status
from supabase import Client

from app.core.security import create_access_token


def login(email: str, password: str, supabase: Client) -> str:
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials") from exc

    if not res.session or not res.session.access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token_expires = timedelta(minutes=60)
    return create_access_token({"sub": email}, expires_delta=access_token_expires)

