from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.bolt_earning import BoltEarning
from app.schemas.bolt_earning import BoltEarningSchema

router = APIRouter(prefix="/bolt", tags=["bolt"])


@router.get("/drivers/{driver_id}/earnings", response_model=list[BoltEarningSchema])
def list_bolt_earnings(
    driver_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    start: datetime = Query(..., alias="from"),
    end: datetime = Query(..., alias="to"),
):
    return (
        db.query(BoltEarning)
        .filter(BoltEarning.org_id == current_user["org_id"])
        .filter(BoltEarning.driver_id == driver_id)
        .filter(BoltEarning.payout_date >= start)
        .filter(BoltEarning.payout_date <= end)
        .order_by(BoltEarning.payout_date.desc())
        .all()
    )

