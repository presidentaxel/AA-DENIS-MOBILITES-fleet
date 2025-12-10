from sqlalchemy import Column, DateTime, Float, String

from app.models import Base


class BoltTrip(Base):
    __tablename__ = "bolt_trips"

    id = Column(String, primary_key=True, index=True)
    org_id = Column(String, nullable=False, index=True)
    driver_id = Column(String, index=True, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    price = Column(Float, default=0)
    distance = Column(Float, default=0)
    currency = Column(String, default="EUR")
    status = Column(String, nullable=True)

