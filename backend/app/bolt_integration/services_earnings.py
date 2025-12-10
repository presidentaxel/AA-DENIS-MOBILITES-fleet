from datetime import datetime
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.bolt_earning import BoltEarning
from app.bolt_integration.bolt_client import BoltClient

settings = get_settings()


def sync_earnings(db: Session, client: BoltClient, driver_id: str | None = None, start: datetime | None = None, end: datetime | None = None) -> None:
    params = {}
    if driver_id:
        params["driver_id"] = driver_id
    if start:
        params["from"] = start.isoformat()
    if end:
        params["to"] = end.isoformat()
    data = client.get("/earnings", params=params)
    earnings = data.get("data", [])
    for e in earnings:
        db.merge(
            BoltEarning(
                id=e["id"],
                org_id=settings.bolt_default_fleet_id or settings.uber_default_org_id or "default_org",
                driver_id=e.get("driver_id"),
                payout_date=datetime.fromisoformat(e["payout_date"]),
                amount=e.get("amount", 0),
                type=e.get("type"),
                currency=e.get("currency", "EUR"),
            )
        )
    db.commit()

