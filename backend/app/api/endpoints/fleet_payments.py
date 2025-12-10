from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.driver_payments import DriverPayment as DriverPaymentModel
from app.schemas.payments import DriverPayment

router = APIRouter()


@router.get("/drivers/{driver_uuid}/payments", response_model=list[DriverPayment])
def driver_payments(
    driver_uuid: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    start: date = Query(..., alias="from"),
    end: date = Query(..., alias="to"),
):
    payments = (
        db.query(DriverPaymentModel)
        .filter(DriverPaymentModel.org_id == current_user["org_id"])
        .filter(DriverPaymentModel.driver_uuid == driver_uuid)
        .filter(DriverPaymentModel.occurred_at >= start)
        .filter(DriverPaymentModel.occurred_at <= end)
        .order_by(DriverPaymentModel.occurred_at.desc())
        .all()
    )
    return payments

