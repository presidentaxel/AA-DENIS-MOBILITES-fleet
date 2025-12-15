# Import de l'ancien système SQLAlchemy (gardé pour référence)
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from app.core.config import get_settings
# settings = get_settings()
# engine = create_engine(settings.database_url, echo=settings.app_env == "dev", future=True)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

# Nouveau système utilisant Supabase API
from app.core.supabase_db import get_db

# Exporter get_db pour compatibilité
__all__ = ['get_db']

