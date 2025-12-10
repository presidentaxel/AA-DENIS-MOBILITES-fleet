from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.driver import UberDriver
from app.uber_integration.uber_client import UberClient

settings = get_settings()


def sync_drivers(db: Session, client: UberClient) -> None:
    data = client.get("/v1/drivers")
    drivers = data.get("data", [])
    for driver in drivers:
        org_id = driver.get("org_id") or settings.uber_default_org_id or "default_org"
        db.merge(
            UberDriver(
                uuid=driver["uuid"],
                org_id=org_id,
                name=driver.get("name") or driver.get("full_name") or "",
                email=driver.get("email"),
            )
        )
    db.commit()

