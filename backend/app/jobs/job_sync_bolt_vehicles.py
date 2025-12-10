from app.core.db import SessionLocal
from app.bolt_integration.bolt_client import BoltClient
from app.bolt_integration.services_vehicles import sync_vehicles


def run():
    with SessionLocal() as db:
        sync_vehicles(db, BoltClient())

