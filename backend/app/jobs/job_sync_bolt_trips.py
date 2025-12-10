from datetime import datetime, timedelta

from app.core.db import SessionLocal
from app.bolt_integration.bolt_client import BoltClient
from app.bolt_integration.services_trips import sync_trips


def run():
    with SessionLocal() as db:
        end = datetime.utcnow()
        start = end - timedelta(hours=6)
        sync_trips(db, BoltClient(), start=start, end=end)

