from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.bolt_driver import BoltDriver
from app.bolt_integration.bolt_client import BoltClient

settings = get_settings()


def sync_drivers(db: Session, client: BoltClient) -> None:
    data = client.get("/drivers")
    drivers = data.get("data", [])
    for d in drivers:
        db.merge(
            BoltDriver(
                id=d["id"],
                org_id=settings.bolt_default_fleet_id or settings.uber_default_org_id or "default_org",
                first_name=d.get("first_name", ""),
                last_name=d.get("last_name", ""),
                email=d.get("email"),
                phone=d.get("phone"),
                active=d.get("active", True),
            )
        )
    db.commit()

