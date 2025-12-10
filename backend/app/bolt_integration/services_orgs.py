from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.org import UberOrganization
from app.bolt_integration.bolt_client import BoltClient

settings = get_settings()


def sync_orgs(db: Session, client: BoltClient) -> None:
    data = client.get("/fleet")
    fleets = data.get("data", [])
    for f in fleets:
        org_id = f.get("id") or settings.uber_default_org_id or "default_org"
        db.merge(UberOrganization(id=f.get("id", org_id), org_id=org_id, name=f.get("name", "Bolt Fleet")))
    db.commit()

