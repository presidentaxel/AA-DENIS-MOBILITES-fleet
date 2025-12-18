from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from app.models import Base


class HeetchSessionCookies(Base):
    """
    Modèle pour stocker les cookies de session Heetch de manière persistante.
    Permet de restaurer la session et éviter de redemander le numéro de téléphone.
    """
    __tablename__ = "heetch_session_cookies"
    
    id = Column(String, primary_key=True, index=True)  # Composite: org_id + phone_number
    org_id = Column(String, nullable=False, index=True)
    phone_number = Column(String, nullable=False)
    cookies = Column(JSONB, nullable=False)  # Stocke les cookies au format JSONB pour Supabase
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

