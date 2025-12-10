from app.core.db import SessionLocal
from app.uber_integration.services_drivers import sync_drivers
from app.uber_integration.uber_client import UberClient


def run():
    with SessionLocal() as db:
        sync_drivers(db, UberClient())

