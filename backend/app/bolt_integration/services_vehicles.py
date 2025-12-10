from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.bolt_vehicle import BoltVehicle
from app.bolt_integration.bolt_client import BoltClient

settings = get_settings()


def sync_vehicles(db: Session, client: BoltClient) -> None:
    data = client.get("/vehicles")
    vehicles = data.get("data", [])
    for v in vehicles:
        db.merge(
            BoltVehicle(
                id=v["id"],
                org_id=settings.uber_default_org_id or "default_org",
                plate=v.get("license_plate", ""),
                model=v.get("model"),
                provider_vehicle_id=v.get("id"),
            )
        )
    db.commit()

