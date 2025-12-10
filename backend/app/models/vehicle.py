from sqlalchemy import Column, String

from app.models import Base


class UberVehicle(Base):
    __tablename__ = "uber_vehicles"

    uuid = Column(String, primary_key=True, index=True)
    org_id = Column(String, nullable=False, index=True)
    plate = Column(String, nullable=False)
    model = Column(String, nullable=True)

