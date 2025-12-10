from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import get_settings
from app.core.security import decode_token

# OAuth2PasswordBearer pour Swagger UI (affiche le bouton Authorize)
# tokenUrl pointe vers /auth/login mais on n'utilise pas le flow OAuth2 complet
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)
settings = get_settings()


def get_current_user(token: str | None = Depends(oauth2_scheme)) -> dict:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(token)
    user = {
        "email": payload.get("sub"),
        "org_id": payload.get("org_id") or settings.uber_default_org_id or "default_org",
    }
    if not user["email"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return user

