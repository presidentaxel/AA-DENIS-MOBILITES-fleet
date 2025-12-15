from sqlalchemy import Column, Float, Integer, String, Boolean, BigInteger
from sqlalchemy.dialects.postgresql import JSONB

from app.models import Base


class BoltOrder(Base):
    """
    Modèle pour les commandes Bolt (orders) depuis getFleetOrders.
    Remplace BoltTrip pour correspondre à la structure réelle de l'API Bolt.
    """
    __tablename__ = "bolt_orders"

    order_reference = Column(String, primary_key=True, index=True)
    org_id = Column(String, nullable=False, index=True)
    company_id = Column(Integer, index=True, nullable=True)
    company_name = Column(String, nullable=True)
    driver_uuid = Column(String, index=True, nullable=True)
    partner_uuid = Column(String, nullable=True)
    driver_name = Column(String, nullable=True)
    driver_phone = Column(String, nullable=True)
    payment_method = Column(String, nullable=True)
    payment_confirmed_timestamp = Column(BigInteger, nullable=True)
    order_created_timestamp = Column(BigInteger, index=True, nullable=True)
    order_status = Column(String, index=True, nullable=True)
    driver_cancelled_reason = Column(String, nullable=True)
    vehicle_model = Column(String, nullable=True)
    vehicle_license_plate = Column(String, nullable=True)
    price_review_reason = Column(String, nullable=True)
    pickup_address = Column(String, nullable=True)
    ride_distance = Column(Float, default=0)
    order_accepted_timestamp = Column(BigInteger, nullable=True)
    order_pickup_timestamp = Column(BigInteger, nullable=True)
    order_drop_off_timestamp = Column(BigInteger, nullable=True)
    order_finished_timestamp = Column(BigInteger, nullable=True)
    # Prix détaillés
    ride_price = Column(Float, default=0)
    booking_fee = Column(Float, default=0)
    toll_fee = Column(Float, default=0)
    cancellation_fee = Column(Float, default=0)
    tip = Column(Float, default=0)
    net_earnings = Column(Float, default=0)
    cash_discount = Column(Float, default=0)
    in_app_discount = Column(Float, default=0)
    commission = Column(Float, default=0)
    currency = Column(String, default="EUR")
    is_scheduled = Column(Boolean, default=False)
    category_name = Column(String, nullable=True)
    category_seats = Column(Integer, nullable=True)
    category_vehicle_type = Column(String, nullable=True)
    # JSON pour order_stops (array complexe)
    order_stops = Column(JSONB, nullable=True)

