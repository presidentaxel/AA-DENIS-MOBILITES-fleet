from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.bolt_driver import BoltDriver
from app.schemas.bolt_driver import BoltDriverSchema

router = APIRouter(prefix="/bolt", tags=["bolt"])


@router.get("/drivers", response_model=list[BoltDriverSchema])
def list_bolt_drivers(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    return (
        db.query(BoltDriver)
        .filter(BoltDriver.org_id == current_user["org_id"])
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/drivers/{driver_id}", response_model=BoltDriverSchema | None)
def get_bolt_driver(driver_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(BoltDriver)
        .filter(BoltDriver.org_id == current_user["org_id"])
        .filter(BoltDriver.id == driver_id)
        .first()
    )

