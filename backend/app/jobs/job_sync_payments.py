from datetime import datetime, timedelta

from app.core.db import SessionLocal
from app.uber_integration.services_payments import sync_payments
from app.uber_integration.uber_client import UberClient


def run():
    since = datetime.utcnow() - timedelta(hours=24)
    with SessionLocal() as db:
        sync_payments(db, UberClient(), since)

