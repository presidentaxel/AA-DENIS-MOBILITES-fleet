from sqlalchemy import Column, DateTime, Float, String

from app.models import Base


class BoltEarning(Base):
    __tablename__ = "bolt_earnings"

    id = Column(String, primary_key=True, index=True)
    org_id = Column(String, nullable=False, index=True)
    driver_id = Column(String, index=True, nullable=True)
    payout_date = Column(DateTime, nullable=False)
    amount = Column(Float, default=0)
    type = Column(String, nullable=True)
    currency = Column(String, default="EUR")

