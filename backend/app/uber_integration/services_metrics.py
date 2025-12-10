from datetime import date
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.driver_metrics import DriverDailyMetrics
from app.uber_integration.uber_client import UberClient

settings = get_settings()


def sync_metrics(db: Session, client: UberClient, start: date, end: date) -> None:
    data = client.get("/v1/metrics", params={"start": start.isoformat(), "end": end.isoformat()})
    metrics = data.get("data", [])
    for row in metrics:
        org_id = row.get("org_id") or settings.uber_default_org_id or "default_org"
        db.merge(
            DriverDailyMetrics(
                id=row["id"],
                org_id=org_id,
                driver_uuid=row["driver_uuid"],
                day=date.fromisoformat(row["day"]),
                trips=row.get("trips", 0),
                online_hours=row.get("online_hours", 0),
                on_trip_hours=row.get("on_trip_hours", 0),
                earnings=row.get("earnings", 0),
            )
        )
    db.commit()

