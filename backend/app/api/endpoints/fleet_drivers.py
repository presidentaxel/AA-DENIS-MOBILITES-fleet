from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.driver import UberDriver
from app.schemas.driver import Driver

router = APIRouter()


@router.get("/drivers", response_model=list[Driver])
def list_drivers(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    drivers = (
        db.query(UberDriver)
        .filter(UberDriver.org_id == current_user["org_id"])
        .offset(offset)
        .limit(limit)
        .all()
    )
    return drivers


@router.get("/drivers/{driver_uuid}", response_model=Driver)
def get_driver(driver_uuid: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    driver = (
        db.query(UberDriver)
        .filter(UberDriver.org_id == current_user["org_id"])
        .filter(UberDriver.uuid == driver_uuid)
        .first()
    )
    return driver

