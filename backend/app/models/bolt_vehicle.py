from sqlalchemy import Column, String

from app.models import Base


class BoltVehicle(Base):
    __tablename__ = "bolt_vehicles"

    id = Column(String, primary_key=True, index=True)
    org_id = Column(String, nullable=False, index=True)
    provider_vehicle_id = Column(String, nullable=True)
    plate = Column(String, nullable=False)
    model = Column(String, nullable=True)

