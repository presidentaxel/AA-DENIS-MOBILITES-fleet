from datetime import timedelta

from fastapi import HTTPException, status
from supabase import Client

from app.core.security import create_access_token
from app.core.supabase_db import SupabaseDB
from app.core.supabase_client import get_supabase_client
from app.core.config import get_settings
from app.bolt_integration.services_sync_all import sync_all_bolt_data
from app.core import logging as app_logging
import threading

settings = get_settings()
logger = app_logging.get_logger(__name__)


def login(email: str, password: str, supabase: Client) -> str:
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials") from exc

    if not res.session or not res.session.access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Déterminer org_id de l'utilisateur (peut être dans les metadata Supabase ou utiliser default)
    org_id = settings.uber_default_org_id or "default_org"
    
    # Récupérer org_id depuis les metadata utilisateur si disponible
    if res.user and res.user.user_metadata:
        org_id = res.user.user_metadata.get("org_id", org_id)
    
    # Créer le token avec org_id
    access_token_expires = timedelta(minutes=60)
    token_payload = {"sub": email, "org_id": org_id}
    token = create_access_token(token_payload, expires_delta=access_token_expires)
    
    # NOTE: La synchronisation automatique est désactivée au login car :
    # - Le scheduler quotidien s'en charge déjà (2h du matin)
    # - Le serveur démarre déjà une sync légère au démarrage
    # - Évite de surcharger l'API Bolt à chaque connexion
    # Pour forcer une sync manuelle, utiliser l'endpoint /bolt/sync/*
    
    return token

