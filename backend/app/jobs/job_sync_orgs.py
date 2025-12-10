from app.core.db import SessionLocal
from app.uber_integration.services_orgs import sync_organizations
from app.uber_integration.uber_client import UberClient


def run():
    with SessionLocal() as db:
        sync_organizations(db, UberClient())

