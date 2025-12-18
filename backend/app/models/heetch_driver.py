from sqlalchemy import Boolean, Column, String

from app.models import Base


class HeetchDriver(Base):
    __tablename__ = "heetch_drivers"

    id = Column(String, primary_key=True, index=True)  # email comme ID
    org_id = Column(String, nullable=False, index=True)
    first_name = Column(String, nullable=False, default="")
    last_name = Column(String, nullable=False, default="")
    email = Column(String, nullable=False, index=True)
    image_url = Column(String, nullable=True)
    active = Column(Boolean, default=True)

