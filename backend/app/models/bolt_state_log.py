from sqlalchemy import Column, Float, String, BigInteger
from sqlalchemy.dialects.postgresql import JSONB

from app.models import Base


class BoltStateLog(Base):
    """
    Modèle pour les logs d'état des drivers Bolt depuis getFleetStateLogs.
    """
    __tablename__ = "bolt_state_logs"

    id = Column(String, primary_key=True, index=True)  # Généré: driver_uuid + created timestamp
    org_id = Column(String, nullable=False, index=True)
    driver_uuid = Column(String, nullable=False, index=True)
    vehicle_uuid = Column(String, index=True, nullable=True)
    created = Column(BigInteger, nullable=False, index=True)
    state = Column(String, nullable=False, index=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    # JSON pour active_categories (structure complexe)
    active_categories = Column(JSONB, nullable=True)

