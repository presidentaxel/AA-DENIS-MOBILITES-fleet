from app.core.db import SessionLocal
from app.bolt_integration.bolt_client import BoltClient
from app.bolt_integration.services_drivers import sync_drivers


def run():
    with SessionLocal() as db:
        sync_drivers(db, BoltClient())

