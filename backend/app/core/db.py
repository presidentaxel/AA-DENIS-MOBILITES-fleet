# Import de l'ancien système SQLAlchemy (gardé pour référence)
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from app.core.config import get_settings
# settings = get_settings()
# engine = create_engine(settings.database_url, echo=settings.app_env == "dev", future=True)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

# Nouveau système utilisant Supabase API
from app.core.supabase_db import get_db, SupabaseDB


class SessionLocal:
    """
    Classe de compatibilité pour remplacer SQLAlchemy SessionLocal.
    Retourne une instance de SupabaseDB pour les jobs qui utilisent encore SessionLocal().
    """
    def __call__(self):
        """Retourne une nouvelle instance de SupabaseDB."""
        return SupabaseDB()
    
    def __enter__(self):
        """Support du context manager."""
        return SupabaseDB()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support du context manager."""
        pass


# Instance singleton pour compatibilité avec l'ancien code
SessionLocal = SessionLocal()

# Exporter get_db et SessionLocal pour compatibilité
__all__ = ['get_db', 'SessionLocal']

