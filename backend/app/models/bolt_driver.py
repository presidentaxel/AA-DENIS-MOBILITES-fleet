from sqlalchemy import Boolean, Column, String

from app.models import Base


class BoltDriver(Base):
    __tablename__ = "bolt_drivers"

    id = Column(String, primary_key=True, index=True)
    org_id = Column(String, nullable=False, index=True)
    first_name = Column(String, nullable=False, default="")
    last_name = Column(String, nullable=False, default="")
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    active = Column(Boolean, default=True)

