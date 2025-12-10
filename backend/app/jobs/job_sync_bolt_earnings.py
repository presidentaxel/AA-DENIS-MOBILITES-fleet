from datetime import datetime, timedelta

from app.core.db import SessionLocal
from app.bolt_integration.bolt_client import BoltClient
from app.bolt_integration.services_earnings import sync_earnings


def run():
    with SessionLocal() as db:
        end = datetime.utcnow()
        start = end - timedelta(hours=24)
        sync_earnings(db, BoltClient(), start=start, end=end)

