from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.vehicle import UberVehicle
from app.schemas.vehicle import Vehicle

router = APIRouter()


@router.get("/vehicles", response_model=list[Vehicle])
def list_vehicles(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(UberVehicle).filter(UberVehicle.org_id == current_user["org_id"]).all()


@router.get("/vehicles/{vehicle_uuid}", response_model=Vehicle)
def get_vehicle(vehicle_uuid: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(UberVehicle)
        .filter(UberVehicle.org_id == current_user["org_id"])
        .filter(UberVehicle.uuid == vehicle_uuid)
        .first()
    )

