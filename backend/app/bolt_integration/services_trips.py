from datetime import datetime
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.bolt_trip import BoltTrip
from app.bolt_integration.bolt_client import BoltClient

settings = get_settings()


def sync_trips(db: Session, client: BoltClient, driver_id: str | None = None, start: datetime | None = None, end: datetime | None = None) -> None:
    params = {}
    if driver_id:
        params["driver_id"] = driver_id
    if start:
        params["from"] = start.isoformat()
    if end:
        params["to"] = end.isoformat()
    data = client.get("/trips", params=params)
    trips = data.get("data", [])
    for t in trips:
        db.merge(
            BoltTrip(
                id=t["id"],
                org_id=settings.uber_default_org_id or "default_org",
                driver_id=t.get("driver_id"),
                start_time=datetime.fromisoformat(t["start_time"]),
                end_time=datetime.fromisoformat(t["end_time"]),
                price=t.get("price", 0),
                distance=t.get("distance", 0),
                currency=t.get("currency", "EUR"),
                status=t.get("status"),
            )
        )
    db.commit()

