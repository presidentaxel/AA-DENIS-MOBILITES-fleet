from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.bolt_vehicle import BoltVehicle
from app.schemas.bolt_vehicle import BoltVehicleSchema

router = APIRouter(prefix="/bolt", tags=["bolt"])


@router.get("/vehicles", response_model=list[BoltVehicleSchema])
def list_bolt_vehicles(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(BoltVehicle).filter(BoltVehicle.org_id == current_user["org_id"]).all()

