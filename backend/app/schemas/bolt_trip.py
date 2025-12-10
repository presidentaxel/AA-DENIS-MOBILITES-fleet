from datetime import datetime

from pydantic import BaseModel


class BoltTripSchema(BaseModel):
    id: str
    org_id: str
    driver_id: str | None = None
    start_time: datetime
    end_time: datetime
    price: float
    distance: float
    currency: str
    status: str | None = None

    class Config:
        from_attributes = True

