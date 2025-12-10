from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.service_auth import login
from app.schemas.auth import TokenResponse
from app.core.supabase_client import get_supabase_client
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login_route(form_data: OAuth2PasswordRequestForm = Depends()):
    supabase = get_supabase_client()
    token = login(form_data.username, form_data.password, supabase)
    return TokenResponse(access_token=token, token_type="bearer")


@router.get("/me", response_model=dict)
def me(current_user: dict = Depends(get_current_user)):
    return {"user": current_user}

