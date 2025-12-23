from datetime import date
from typing import Optional

from pydantic import BaseModel


class HeetchEarningBase(BaseModel):
    driver_id: str
    date: date
    period: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    gross_earnings: float = 0
    net_earnings: float = 0
    cash_collected: float = 0
    card_gross_earnings: float = 0
    cash_commission_fees: float = 0
    card_commission_fees: float = 0
    cancellation_fees: float = 0
    cancellation_fee_adjustments: float = 0
    bonuses: float = 0
    terminated_rides: int = 0
    cancelled_rides: int = 0
    cash_discount: float = 0
    unpaid_cash_rides_refunds: Optional[float] = None
    debt: Optional[float] = None
    money_transfer_amount: Optional[float] = None
    currency: str = "EUR"


class HeetchEarningCreate(HeetchEarningBase):
    org_id: str


class HeetchEarningSchema(HeetchEarningBase):
    id: str
    org_id: str

    class Config:
        from_attributes = True

