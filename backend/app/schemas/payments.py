from datetime import datetime

from pydantic import BaseModel


class DriverPayment(BaseModel):
    id: str | None = None
    org_id: str
    driver_uuid: str
    occurred_at: datetime
    amount: float
    currency: str = "EUR"
    description: str | None = None

    class Config:
        from_attributes = True

