from sqlalchemy import Column, Date, Float, String

from app.models import Base


class DriverDailyMetrics(Base):
    __tablename__ = "driver_daily_metrics"

    id = Column(String, primary_key=True)
    org_id = Column(String, nullable=False, index=True)
    driver_uuid = Column(String, index=True, nullable=False)
    day = Column(Date, index=True, nullable=False)
    trips = Column(Float, default=0)
    online_hours = Column(Float, default=0)
    on_trip_hours = Column(Float, default=0)
    earnings = Column(Float, default=0)

