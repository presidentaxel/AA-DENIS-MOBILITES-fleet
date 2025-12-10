from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.driver_metrics import DriverDailyMetrics
from app.schemas.metrics import DriverMetrics

router = APIRouter()


@router.get("/drivers/{driver_uuid}/metrics", response_model=list[DriverMetrics])
def driver_metrics(
    driver_uuid: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    start: date = Query(..., alias="from"),
    end: date = Query(..., alias="to"),
):
    metrics = (
        db.query(DriverDailyMetrics)
        .filter(DriverDailyMetrics.org_id == current_user["org_id"])
        .filter(DriverDailyMetrics.driver_uuid == driver_uuid)
        .filter(DriverDailyMetrics.day >= start)
        .filter(DriverDailyMetrics.day <= end)
        .order_by(DriverDailyMetrics.day.desc())
        .all()
    )
    return metrics

