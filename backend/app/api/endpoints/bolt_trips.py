from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.core.db import get_db
from app.core.supabase_db import SupabaseDB
from app.models.bolt_order import BoltOrder
from app.schemas.bolt_order import BoltOrderSchema

router = APIRouter(prefix="/bolt", tags=["bolt"])


@router.get("/drivers/{driver_id}/orders", response_model=list[BoltOrderSchema])
def list_bolt_orders(
    driver_id: str,
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db),
    start: datetime = Query(..., alias="from"),
    end: datetime = Query(..., alias="to"),
):
    """Liste les commandes (orders) Bolt pour un driver donné."""
    from datetime import timezone
    
    # Parse dates: treat naive datetime as local dates
    if start.tzinfo is None:
        start = start.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    else:
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if end.tzinfo is None:
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc)
    else:
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    start_ts = int(start.timestamp())
    end_ts = int(end.timestamp())
    
    results = (
        db.query(BoltOrder)
        .filter(BoltOrder.org_id == current_user["org_id"])
        .filter(BoltOrder.driver_uuid == driver_id)
        .filter(BoltOrder.order_created_timestamp >= start_ts)
        .filter(BoltOrder.order_created_timestamp <= end_ts)
        .order_by(BoltOrder.order_created_timestamp.desc())
        .all()
    )
    
    # Additional safety check
    results = [order for order in results if order.driver_uuid == driver_id]
    
    return results


@router.get("/orders", response_model=list[BoltOrderSchema])
def list_all_bolt_orders(
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db),
    start: datetime = Query(..., alias="from"),
    end: datetime = Query(..., alias="to"),
    driver_uuid: str | None = Query(None, description="Filtrer par driver UUID"),
):
    """Liste toutes les commandes (orders) Bolt pour l'organisation."""
    from datetime import timezone
    
    # Parse dates: treat naive datetime as local dates
    if start.tzinfo is None:
        start = start.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    else:
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if end.tzinfo is None:
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc)
    else:
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    start_ts = int(start.timestamp())
    end_ts = int(end.timestamp())
    
    query = (
        db.query(BoltOrder)
        .filter(BoltOrder.org_id == current_user["org_id"])
        .filter(BoltOrder.order_created_timestamp >= start_ts)
        .filter(BoltOrder.order_created_timestamp <= end_ts)
    )
    
    # IMPORTANT: Always filter by driver_uuid if provided
    if driver_uuid:
        query = query.filter(BoltOrder.driver_uuid == driver_uuid)
    
    results = query.order_by(BoltOrder.order_created_timestamp.desc()).all()
    
    # Additional safety check: filter results again by driver_uuid if provided
    # This ensures no orders from other drivers leak through
    if driver_uuid:
        results = [order for order in results if order.driver_uuid == driver_uuid]
    
    return results

