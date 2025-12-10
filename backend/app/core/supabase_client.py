from supabase import Client, create_client

from app.core.config import get_settings

settings = get_settings()


def get_supabase_client() -> Client:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("Supabase configuration missing")
    return create_client(str(settings.supabase_url), settings.supabase_service_role_key)

