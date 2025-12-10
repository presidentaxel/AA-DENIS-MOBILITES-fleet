from app.core.db import SessionLocal
from app.uber_integration.services_vehicles import sync_vehicles
from app.uber_integration.uber_client import UberClient


def run():
    with SessionLocal() as db:
        sync_vehicles(db, UberClient())

