from datetime import datetime

from pydantic import BaseModel


class BoltEarningSchema(BaseModel):
    id: str
    org_id: str
    driver_id: str | None = None
    payout_date: datetime
    amount: float
    type: str | None = None
    currency: str

    class Config:
        from_attributes = True

