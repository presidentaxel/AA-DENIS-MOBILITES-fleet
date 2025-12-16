from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.core.db import get_db
from app.core.supabase_db import SupabaseDB
from app.models.bolt_state_log import BoltStateLog
from app.schemas.bolt_state_log import BoltStateLogSchema

router = APIRouter(prefix="/bolt", tags=["bolt"])


@router.get("/drivers/{driver_id}/state-logs", response_model=list[BoltStateLogSchema])
def list_bolt_state_logs(
    driver_id: str,
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db),
    start: datetime = Query(..., alias="from"),
    end: datetime = Query(..., alias="to"),
):
    """Liste les logs d'état Bolt pour un driver donné."""
    from datetime import timezone
    
    # Parse dates: FastAPI gives us naive datetime for YYYY-MM-DD format
    # We interpret them as local dates (start and end of day in local timezone)
    # Then convert to UTC timestamps for comparison with stored timestamps
    
    # If naive datetime (from YYYY-MM-DD), treat as local timezone start/end of day
    if start.tzinfo is None:
        # Start of day in local timezone
        start_local = start.replace(hour=0, minute=0, second=0, microsecond=0)
        # Convert local to UTC (assuming server is in UTC or we want to treat as UTC)
        start = start_local.replace(tzinfo=timezone.utc)
    else:
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if end.tzinfo is None:
        # End of day in local timezone
        end_local = end.replace(hour=23, minute=59, second=59, microsecond=999999)
        # Convert local to UTC
        end = end_local.replace(tzinfo=timezone.utc)
    else:
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    start_ts = int(start.timestamp())
    end_ts = int(end.timestamp())
    
    # Double check: ensure we filter by the correct driver
    query = (
        db.query(BoltStateLog)
        .filter(BoltStateLog.org_id == current_user["org_id"])
        .filter(BoltStateLog.driver_uuid == driver_id)
        .filter(BoltStateLog.created >= start_ts)
        .filter(BoltStateLog.created <= end_ts)
        .order_by(BoltStateLog.created.desc())
    )
    
    results = query.all()
    
    # Additional safety check: filter results to ensure driver_uuid matches
    # (in case of any edge cases)
    results = [log for log in results if log.driver_uuid == driver_id]
    
    return results


@router.get("/state-logs", response_model=list[BoltStateLogSchema])
def list_all_bolt_state_logs(
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db),
    start: datetime = Query(..., alias="from"),
    end: datetime = Query(..., alias="to"),
    driver_uuid: str | None = Query(None, description="Filtrer par driver UUID"),
    state: str | None = Query(None, description="Filtrer par état (active, inactive, etc.)"),
):
    """Liste tous les logs d'état Bolt pour l'organisation."""
    start_ts = int(start.timestamp())
    end_ts = int(end.timestamp())
    
    query = (
        db.query(BoltStateLog)
        .filter(BoltStateLog.org_id == current_user["org_id"])
        .filter(BoltStateLog.created >= start_ts)
        .filter(BoltStateLog.created <= end_ts)
    )
    
    if driver_uuid:
        query = query.filter(BoltStateLog.driver_uuid == driver_uuid)
    
    if state:
        query = query.filter(BoltStateLog.state == state)
    
    return query.order_by(BoltStateLog.created.desc()).all()

