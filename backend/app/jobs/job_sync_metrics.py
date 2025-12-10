from datetime import date, timedelta

from app.core.db import SessionLocal
from app.uber_integration.services_metrics import sync_metrics
from app.uber_integration.uber_client import UberClient


def run():
    today = date.today()
    with SessionLocal() as db:
        sync_metrics(db, UberClient(), today - timedelta(days=1), today)

