from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.core.db import get_db
from app.bolt_integration.bolt_client import BoltClient
from app.bolt_integration.services_drivers import sync_drivers
from app.bolt_integration.services_earnings import sync_earnings
from app.bolt_integration.services_trips import sync_trips
from app.bolt_integration.services_vehicles import sync_vehicles

router = APIRouter(prefix="/bolt", tags=["bolt"])


@router.post("/sync/drivers")
def sync_bolt_drivers(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    """Synchronise les chauffeurs Bolt depuis l'API Bolt vers la base de données locale."""
    try:
        sync_drivers(db, BoltClient())
        return {"status": "success", "message": "Drivers synchronized"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/sync/vehicles")
def sync_bolt_vehicles(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    """Synchronise les véhicules Bolt depuis l'API Bolt vers la base de données locale."""
    try:
        sync_vehicles(db, BoltClient())
        return {"status": "success", "message": "Vehicles synchronized"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/sync/trips")
def sync_bolt_trips(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
    driver_id: str | None = Query(None, description="ID du chauffeur (optionnel)"),
    from_date: datetime | None = Query(None, alias="from", description="Date de début (ISO 8601)"),
    to_date: datetime | None = Query(None, alias="to", description="Date de fin (ISO 8601)"),
):
    """Synchronise les trajets Bolt depuis l'API Bolt vers la base de données locale."""
    try:
        # Par défaut, sync les 7 derniers jours
        if not from_date:
            from_date = datetime.utcnow() - timedelta(days=7)
        if not to_date:
            to_date = datetime.utcnow()
        
        sync_trips(db, BoltClient(), driver_id=driver_id, start=from_date, end=to_date)
        return {"status": "success", "message": "Trips synchronized"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/sync/earnings")
def sync_bolt_earnings(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
    driver_id: str | None = Query(None, description="ID du chauffeur (optionnel)"),
    from_date: datetime | None = Query(None, alias="from", description="Date de début (ISO 8601)"),
    to_date: datetime | None = Query(None, alias="to", description="Date de fin (ISO 8601)"),
):
    """Synchronise les revenus Bolt depuis l'API Bolt vers la base de données locale."""
    try:
        # Par défaut, sync les 30 derniers jours
        if not from_date:
            from_date = datetime.utcnow() - timedelta(days=30)
        if not to_date:
            to_date = datetime.utcnow()
        
        sync_earnings(db, BoltClient(), driver_id=driver_id, start=from_date, end=to_date)
        return {"status": "success", "message": "Earnings synchronized"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

