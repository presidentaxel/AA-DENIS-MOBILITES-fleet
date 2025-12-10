from sqlalchemy import Column, String

from app.models import Base


class UberOrganization(Base):
    __tablename__ = "uber_organizations"

    id = Column(String, primary_key=True, index=True)
    org_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)

