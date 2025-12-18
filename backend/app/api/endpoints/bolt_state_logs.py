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
    # The timestamps in the database (created) are Unix timestamps in UTC
    # We need to interpret the dates as the start/end of day in UTC
    # Since the frontend sends YYYY-MM-DD, we treat it as a date (not datetime)
    # and convert to UTC timestamps for the start and end of that day
    
    # If naive datetime (from YYYY-MM-DD), treat as date and convert to UTC day boundaries
    if start.tzinfo is None:
        # Treat as start of day in UTC (00:00:00 UTC)
        start = start.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    else:
        # Already has timezone, ensure it's start of day
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if end.tzinfo is None:
        # Treat as end of day in UTC (23:59:59.999999 UTC)
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc)
    else:
        # Already has timezone, ensure it's end of day
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # Convert to Unix timestamps (seconds since epoch, UTC)
    # These timestamps will be compared directly with the 'created' column (bigint)
    start_ts = int(start.timestamp())
    end_ts = int(end.timestamp())
    
    # Debug: log the date range being queried
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Querying state logs for driver {driver_id} from {start.date()} (ts: {start_ts}) to {end.date()} (ts: {end_ts})")
    
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
    logger.info(f"Found {len(results)} state logs for driver {driver_id} in date range")
    
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

