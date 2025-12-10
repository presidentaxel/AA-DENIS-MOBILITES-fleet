from sqlalchemy import Column, DateTime, Float, String

from app.models import Base


class DriverPayment(Base):
    __tablename__ = "driver_payments"

    id = Column(String, primary_key=True)
    org_id = Column(String, nullable=False, index=True)
    driver_uuid = Column(String, index=True, nullable=False)
    occurred_at = Column(DateTime, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="EUR")
    description = Column(String, nullable=True)

