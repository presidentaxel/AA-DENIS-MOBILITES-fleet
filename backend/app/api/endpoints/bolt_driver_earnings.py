from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.core.db import get_db
from app.core.supabase_db import SupabaseDB
from app.models.bolt_order import BoltOrder
from app.models.bolt_driver import BoltDriver
from app.schemas.bolt_driver_earnings import BoltDriverEarningsSchema

router = APIRouter(prefix="/bolt", tags=["bolt"])


@router.get("/drivers/{driver_id}/earnings", response_model=BoltDriverEarningsSchema)
def get_bolt_driver_earnings(
    driver_id: str,
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db),
    start: Optional[datetime] = Query(None, alias="from", description="Date de début (ISO 8601)"),
    end: Optional[datetime] = Query(None, alias="to", description="Date de fin (ISO 8601)"),
):
    """
    Calcule les revenus agrégés d'un driver Bolt sur une période donnée.
    Inclut : nombre d'orders, revenus nets, commissions, cash, etc.
    """
    # Récupérer les infos du driver
    driver = db.query(BoltDriver).filter(
        BoltDriver.id == driver_id,
        BoltDriver.org_id == current_user["org_id"]
    ).first()
    
    if not driver:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Driver not found")
    
    # Par défaut, les 30 derniers jours
    if not end:
        end = datetime.utcnow()
    if not start:
        from datetime import timedelta
        start = end - timedelta(days=30)
    
    start_ts = int(start.timestamp())
    end_ts = int(end.timestamp())
    
    # Récupérer tous les orders du driver pour cette période
    orders = db.query(BoltOrder).filter(
        BoltOrder.org_id == current_user["org_id"],
        BoltOrder.driver_uuid == driver_id,
        BoltOrder.order_created_timestamp >= start_ts,
        BoltOrder.order_created_timestamp <= end_ts
    ).all()
    
    # Calculer les statistiques
    total_orders = len(orders)
    completed_orders = sum(1 for o in orders if o.order_status and "finished" in o.order_status.lower())
    cancelled_orders = sum(1 for o in orders if o.order_status and "cancel" in o.order_status.lower())
    
    # Revenus
    total_net_earnings = sum(o.net_earnings or 0 for o in orders)
    total_ride_price = sum(o.ride_price or 0 for o in orders)
    total_booking_fee = sum(o.booking_fee or 0 for o in orders)
    total_toll_fee = sum(o.toll_fee or 0 for o in orders)
    total_tip = sum(o.tip or 0 for o in orders)
    total_cancellation_fee = sum(o.cancellation_fee or 0 for o in orders)
    
    # Dépenses/déductions
    total_commission = sum(o.commission or 0 for o in orders)
    total_cash_discount = sum(o.cash_discount or 0 for o in orders)
    total_in_app_discount = sum(o.in_app_discount or 0 for o in orders)
    
    # Métriques
    total_distance = sum(o.ride_distance or 0 for o in orders)
    average_order_value = total_ride_price / total_orders if total_orders > 0 else 0.0
    average_net_earnings_per_order = total_net_earnings / total_orders if total_orders > 0 else 0.0
    
    # Nom du driver depuis les orders (ou depuis la table drivers)
    driver_name = None
    if orders:
        driver_name = orders[0].driver_name
    if not driver_name:
        driver_name = f"{driver.first_name} {driver.last_name}".strip() if driver.first_name or driver.last_name else None
    
    return BoltDriverEarningsSchema(
        driver_uuid=driver_id,
        driver_name=driver_name,
        org_id=current_user["org_id"],
        total_orders=total_orders,
        completed_orders=completed_orders,
        cancelled_orders=cancelled_orders,
        total_net_earnings=round(total_net_earnings, 2),
        total_ride_price=round(total_ride_price, 2),
        total_booking_fee=round(total_booking_fee, 2),
        total_toll_fee=round(total_toll_fee, 2),
        total_tip=round(total_tip, 2),
        total_cancellation_fee=round(total_cancellation_fee, 2),
        total_commission=round(total_commission, 2),
        total_cash_discount=round(total_cash_discount, 2),
        total_in_app_discount=round(total_in_app_discount, 2),
        total_distance=round(total_distance, 2),
        average_order_value=round(average_order_value, 2),
        average_net_earnings_per_order=round(average_net_earnings_per_order, 2),
        period_start=start,
        period_end=end,
        currency="EUR",
    )


@router.get("/drivers/{driver_id}/orders/stats")
def get_bolt_driver_orders_stats(
    driver_id: str,
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db),
    start: Optional[datetime] = Query(None, alias="from", description="Date de début (ISO 8601)"),
    end: Optional[datetime] = Query(None, alias="to", description="Date de fin (ISO 8601)"),
):
    """
    Retourne des statistiques détaillées sur les orders d'un driver.
    Version simplifiée avec juste les compteurs.
    """
    # Par défaut, les 30 derniers jours
    if not end:
        end = datetime.utcnow()
    if not start:
        from datetime import timedelta
        start = end - timedelta(days=30)
    
    start_ts = int(start.timestamp())
    end_ts = int(end.timestamp())
    
    # Récupérer tous les orders du driver pour cette période
    orders = db.query(BoltOrder).filter(
        BoltOrder.org_id == current_user["org_id"],
        BoltOrder.driver_uuid == driver_id,
        BoltOrder.order_created_timestamp >= start_ts,
        BoltOrder.order_created_timestamp <= end_ts
    ).all()
    
    # Compter par statut
    status_counts = {}
    for order in orders:
        status = order.order_status or "unknown"
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return {
        "driver_uuid": driver_id,
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "total_orders": len(orders),
        "status_breakdown": status_counts,
        "total_net_earnings": round(sum(o.net_earnings or 0 for o in orders), 2),
        "total_commission": round(sum(o.commission or 0 for o in orders), 2),
    }

