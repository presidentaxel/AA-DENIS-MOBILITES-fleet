from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class OrderStopSchema(BaseModel):
    type: str
    lng: float
    lat: float
    real_lng: Optional[float] = None
    real_lat: Optional[float] = None


class BoltOrderSchema(BaseModel):
    order_reference: str
    org_id: str
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    driver_uuid: Optional[str] = None
    partner_uuid: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    payment_method: Optional[str] = None
    payment_confirmed_timestamp: Optional[int] = None
    order_created_timestamp: Optional[int] = None
    order_status: Optional[str] = None
    driver_cancelled_reason: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_license_plate: Optional[str] = None
    price_review_reason: Optional[str] = None
    pickup_address: Optional[str] = None
    ride_distance: Optional[float] = 0
    order_accepted_timestamp: Optional[int] = None
    order_pickup_timestamp: Optional[int] = None
    order_drop_off_timestamp: Optional[int] = None
    order_finished_timestamp: Optional[int] = None
    ride_price: Optional[float] = 0
    booking_fee: Optional[float] = 0
    toll_fee: Optional[float] = 0
    cancellation_fee: Optional[float] = 0
    tip: Optional[float] = 0
    net_earnings: Optional[float] = 0
    cash_discount: Optional[float] = 0
    in_app_discount: Optional[float] = 0
    commission: Optional[float] = 0
    currency: Optional[str] = "EUR"
    is_scheduled: Optional[bool] = False
    category_name: Optional[str] = None
    category_seats: Optional[int] = None
    category_vehicle_type: Optional[str] = None
    order_stops: Optional[List[Dict[str, Any]]] = None

    class Config:
        from_attributes = True

