from sqlalchemy import Column, Date, Float, Integer, String

from app.models import Base


class HeetchEarning(Base):
    """
    Modèle pour les earnings Heetch depuis l'API /api/earnings.
    Stocke les revenus par driver, date et période (weekly/monthly).
    """
    __tablename__ = "heetch_earnings"

    id = Column(String, primary_key=True, index=True)  # Composite: driver_id_date_period
    org_id = Column(String, nullable=False, index=True)
    driver_id = Column(String, index=True, nullable=False)  # email du driver
    date = Column(Date, nullable=False, index=True)  # Date de début de la période
    period = Column(String, nullable=False, index=True)  # weekly, monthly, etc.
    start_date = Column(Date, nullable=True, index=True)  # Date de début réelle de la période (depuis summary)
    end_date = Column(Date, nullable=True, index=True)  # Date de fin réelle de la période (depuis summary)
    
    # Earnings détaillés
    gross_earnings = Column(Float, default=0)
    net_earnings = Column(Float, default=0)
    cash_collected = Column(Float, default=0)
    card_gross_earnings = Column(Float, default=0)
    cash_commission_fees = Column(Float, default=0)
    card_commission_fees = Column(Float, default=0)
    cancellation_fees = Column(Float, default=0)
    cancellation_fee_adjustments = Column(Float, default=0)
    bonuses = Column(Float, default=0)
    terminated_rides = Column(Integer, default=0)  # Nombre de courses terminées
    cancelled_rides = Column(Integer, default=0)  # Nombre de courses annulées
    cash_discount = Column(Float, default=0)
    unpaid_cash_rides_refunds = Column(Float, nullable=True)  # Peut être null
    debt = Column(Float, nullable=True)  # Peut être null
    money_transfer_amount = Column(Float, nullable=True)  # Peut être null
    currency = Column(String, default="EUR")

