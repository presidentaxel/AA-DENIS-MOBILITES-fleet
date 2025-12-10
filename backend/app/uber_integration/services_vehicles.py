from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.vehicle import UberVehicle
from app.uber_integration.uber_client import UberClient

settings = get_settings()


def sync_vehicles(db: Session, client: UberClient) -> None:
    data = client.get("/v1/vehicles")
    vehicles = data.get("data", [])
    for veh in vehicles:
        org_id = veh.get("org_id") or settings.uber_default_org_id or "default_org"
        db.merge(
            UberVehicle(
                uuid=veh["uuid"],
                org_id=org_id,
                plate=veh.get("license_plate", ""),
                model=veh.get("model"),
            )
        )
    db.commit()

