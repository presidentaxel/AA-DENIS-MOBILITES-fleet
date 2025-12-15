from sqlalchemy import Column, String

from app.models import Base


class BoltOrganization(Base):
    __tablename__ = "bolt_organizations"

    id = Column(String, primary_key=True, index=True)  # company_id comme string
    org_id = Column(String, nullable=False, index=True)  # org_id interne pour RLS
    name = Column(String, nullable=True)  # Optionnel, peut être récupéré depuis l'API si disponible

