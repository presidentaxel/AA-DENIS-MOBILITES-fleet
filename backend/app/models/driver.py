from sqlalchemy import Column, String

from app.models import Base


class UberDriver(Base):
    __tablename__ = "uber_drivers"

    uuid = Column(String, primary_key=True, index=True)
    org_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)

