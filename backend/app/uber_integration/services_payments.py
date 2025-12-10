from datetime import datetime
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.driver_payments import DriverPayment
from app.uber_integration.uber_client import UberClient

settings = get_settings()


def sync_payments(db: Session, client: UberClient, since: datetime) -> None:
    data = client.get("/v1/payments", params={"since": since.isoformat()})
    payments = data.get("data", [])
    for p in payments:
        org_id = p.get("org_id") or settings.uber_default_org_id or "default_org"
        db.merge(
            DriverPayment(
                id=p["id"],
                org_id=org_id,
                driver_uuid=p["driver_uuid"],
                occurred_at=datetime.fromisoformat(p["occurred_at"]),
                amount=p.get("amount", 0),
                currency=p.get("currency", "EUR"),
                description=p.get("description"),
            )
        )
    db.commit()

