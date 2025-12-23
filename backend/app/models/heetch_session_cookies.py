from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from datetime import datetime
import uuid
from app.models import Base


class HeetchSessionCookies(Base):
    """
    Modèle pour stocker les cookies de session Heetch de manière persistante.
    Permet de restaurer la session et éviter de redemander le numéro de téléphone.
    """
    __tablename__ = "heetch_session_cookies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    org_id = Column(String, nullable=False, index=True)
    phone_number = Column(String, nullable=False)
    cookies = Column(JSONB, nullable=False)  # Stocke les cookies au format JSONB pour Supabase
    expires_at = Column(DateTime, nullable=False, index=True)
    invalid_at = Column(DateTime, nullable=True, index=True)  # Date à laquelle les cookies ont été marqués comme invalides (HTTP 307). NULL = cookies valides.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

