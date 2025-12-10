from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.org import UberOrganization
from app.uber_integration.uber_client import UberClient

settings = get_settings()


def sync_organizations(db: Session, client: UberClient) -> None:
    data = client.get("/v1/organizations")
    orgs = data.get("data", [])
    for org in orgs:
        org_id = org.get("org_id") or settings.uber_default_org_id or "default_org"
        db.merge(UberOrganization(id=org["id"], org_id=org_id, name=org.get("name", "")))
    db.commit()

