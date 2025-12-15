from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class BoltDriverEarningsSchema(BaseModel):
    """Schéma pour les revenus agrégés d'un driver Bolt."""
    driver_uuid: str
    driver_name: Optional[str] = None
    org_id: str
    
    # Statistiques générales
    total_orders: int = 0
    completed_orders: int = 0
    cancelled_orders: int = 0
    
    # Revenus
    total_net_earnings: float = 0.0
    total_ride_price: float = 0.0
    total_booking_fee: float = 0.0
    total_toll_fee: float = 0.0
    total_tip: float = 0.0
    total_cancellation_fee: float = 0.0
    
    # Dépenses/déductions
    total_commission: float = 0.0
    total_cash_discount: float = 0.0
    total_in_app_discount: float = 0.0
    
    # Métriques
    total_distance: float = 0.0
    average_order_value: float = 0.0
    average_net_earnings_per_order: float = 0.0
    
    # Période
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    
    currency: str = "EUR"

    class Config:
        from_attributes = True

