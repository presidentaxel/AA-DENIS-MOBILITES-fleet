from datetime import date

from pydantic import BaseModel


class DriverMetrics(BaseModel):
    org_id: str
    driver_uuid: str
    day: date
    trips: float = 0
    online_hours: float = 0
    on_trip_hours: float = 0
    earnings: float = 0

    class Config:
        from_attributes = True

