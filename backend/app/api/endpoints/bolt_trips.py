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
    start_ts = int(start.timestamp())
    end_ts = int(end.timestamp())
    
    return (
        db.query(BoltOrder)
        .filter(BoltOrder.org_id == current_user["org_id"])
        .filter(BoltOrder.driver_uuid == driver_id)
        .filter(BoltOrder.order_created_timestamp >= start_ts)
        .filter(BoltOrder.order_created_timestamp <= end_ts)
        .order_by(BoltOrder.order_created_timestamp.desc())
        .all()
    )


@router.get("/orders", response_model=list[BoltOrderSchema])
def list_all_bolt_orders(
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db),
    start: datetime = Query(..., alias="from"),
    end: datetime = Query(..., alias="to"),
    driver_uuid: str | None = Query(None, description="Filtrer par driver UUID"),
):
    """Liste toutes les commandes (orders) Bolt pour l'organisation."""
    start_ts = int(start.timestamp())
    end_ts = int(end.timestamp())
    
    query = (
        db.query(BoltOrder)
        .filter(BoltOrder.org_id == current_user["org_id"])
        .filter(BoltOrder.order_created_timestamp >= start_ts)
        .filter(BoltOrder.order_created_timestamp <= end_ts)
    )
    
    if driver_uuid:
        query = query.filter(BoltOrder.driver_uuid == driver_uuid)
    
    return query.order_by(BoltOrder.order_created_timestamp.desc()).all()

