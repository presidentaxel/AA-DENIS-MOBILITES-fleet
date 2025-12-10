from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.bolt_trip import BoltTrip
from app.schemas.bolt_trip import BoltTripSchema

router = APIRouter(prefix="/bolt", tags=["bolt"])


@router.get("/drivers/{driver_id}/trips", response_model=list[BoltTripSchema])
def list_bolt_trips(
    driver_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    start: datetime = Query(..., alias="from"),
    end: datetime = Query(..., alias="to"),
):
    return (
        db.query(BoltTrip)
        .filter(BoltTrip.org_id == current_user["org_id"])
        .filter(BoltTrip.driver_id == driver_id)
        .filter(BoltTrip.start_time >= start)
        .filter(BoltTrip.end_time <= end)
        .order_by(BoltTrip.start_time.desc())
        .all()
    )

