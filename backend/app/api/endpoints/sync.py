from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.core.db import get_db
from app.uber_integration.services_drivers import sync_drivers
from app.uber_integration.services_metrics import sync_metrics
from app.uber_integration.services_orgs import sync_organizations
from app.uber_integration.services_payments import sync_payments
from app.uber_integration.services_vehicles import sync_vehicles
from app.uber_integration.uber_client import UberClient

router = APIRouter()


@router.post("/sync/orgs")
def sync_orgs(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    sync_organizations(db, UberClient())
    return {"status": "queued"}


@router.post("/sync/drivers")
def sync_drivers_endpoint(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    sync_drivers(db, UberClient())
    return {"status": "queued"}


@router.post("/sync/vehicles")
def sync_vehicles_endpoint(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    sync_vehicles(db, UberClient())
    return {"status": "queued"}


@router.post("/sync/metrics")
def sync_metrics_endpoint(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    today = date.today()
    sync_metrics(db, UberClient(), today - timedelta(days=1), today)
    return {"status": "queued"}


@router.post("/sync/payments")
def sync_payments_endpoint(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    since = datetime.utcnow() - timedelta(hours=24)
    sync_payments(db, UberClient(), since)
    return {"status": "queued"}

