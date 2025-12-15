from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.core.db import get_db
from app.bolt_integration.bolt_client import BoltClient
from app.bolt_integration.services_drivers import sync_drivers
from app.bolt_integration.services_orgs import sync_orgs
from app.bolt_integration.services_trips import sync_trips
from app.bolt_integration.services_vehicles import sync_vehicles
from app.bolt_integration.services_state_logs import sync_state_logs
from app.jobs.background_tasks import sync_bolt_heavy_data_async, sync_orders_in_batches, sync_state_logs_in_batches

router = APIRouter(prefix="/bolt", tags=["bolt"])


@router.post("/sync/orgs")
def sync_bolt_orgs(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Synchronise les organizations Bolt (company_ids) depuis l'API Bolt vers la base de données locale."""
    try:
        sync_orgs(db, BoltClient(), org_id=current_user["org_id"])
        from app.models.bolt_org import BoltOrganization
        orgs = db.query(BoltOrganization).filter(BoltOrganization.org_id == current_user["org_id"]).all()
        return {
            "status": "success",
            "message": "Organizations synchronized",
            "organizations": [
                {"id": org.id, "org_id": org.org_id, "name": org.name}
                for org in orgs
            ],
            "company_ids": [org.id for org in orgs],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/sync/drivers")
def sync_bolt_drivers(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
    company_id: str | None = Query(None, description="Company ID Bolt (optionnel, utilise BOLT_DEFAULT_FLEET_ID si non fourni)"),
):
    """Synchronise les chauffeurs Bolt depuis l'API Bolt vers la base de données locale."""
    try:
        from app.models.bolt_driver import BoltDriver
        
        # Compter AVANT la sync
        count_before = db.query(BoltDriver).filter(BoltDriver.org_id == current_user["org_id"]).count()
        
        # Synchroniser
        sync_drivers(db, BoltClient(), company_id=company_id, org_id=current_user["org_id"])
        
        # Compter APRÈS la sync
        count_after = db.query(BoltDriver).filter(BoltDriver.org_id == current_user["org_id"]).count()
        
        # Vérifier aussi le total sans filtre org_id pour debug
        total_all = db.query(BoltDriver).count()
        
        return {
            "status": "success",
            "message": "Drivers synchronized",
            "count_before": count_before,
            "count_after": count_after,
            "total_drivers_in_db": count_after,
            "total_all_drivers": total_all,  # Total sans filtre org_id pour debug
            "org_id_used": current_user["org_id"],
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }


@router.post("/sync/vehicles")
def sync_bolt_vehicles(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
    company_id: str | None = Query(None, description="Company ID Bolt (optionnel, utilise BOLT_DEFAULT_FLEET_ID si non fourni)"),
):
    """Synchronise les véhicules Bolt depuis l'API Bolt vers la base de données locale."""
    try:
        sync_vehicles(db, BoltClient(), company_id=company_id, org_id=current_user["org_id"])
        from app.models.bolt_vehicle import BoltVehicle
        total = db.query(BoltVehicle).filter(BoltVehicle.org_id == current_user["org_id"]).count()
        return {
            "status": "success",
            "message": "Vehicles synchronized",
            "total_vehicles_in_db": total,
            "org_id_used": current_user["org_id"],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/sync/orders")
def sync_bolt_orders(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
    company_id: str | None = Query(None, description="Company ID Bolt (optionnel)"),
    from_date: datetime | None = Query(None, alias="from", description="Date de début (ISO 8601)"),
    to_date: datetime | None = Query(None, alias="to", description="Date de fin (ISO 8601)"),
):
    """Synchronise les commandes (orders) Bolt depuis l'API Bolt vers la base de données locale."""
    try:
        # Par défaut, sync les 30 derniers jours
        if not from_date:
            from_date = datetime.utcnow() - timedelta(days=30)
        if not to_date:
            to_date = datetime.utcnow()
        
        sync_trips(db, BoltClient(), company_id=company_id, start=from_date, end=to_date, org_id=current_user["org_id"])
        from app.models.bolt_order import BoltOrder
        total = db.query(BoltOrder).filter(BoltOrder.org_id == current_user["org_id"]).count()
        return {
            "status": "success",
            "message": "Orders synchronized",
            "total_orders_in_db": total,
            "org_id_used": current_user["org_id"],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/sync/state-logs")
def sync_bolt_state_logs(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
    company_id: str | None = Query(None, description="Company ID Bolt (optionnel)"),
    from_date: datetime | None = Query(None, alias="from", description="Date de début (ISO 8601)"),
    to_date: datetime | None = Query(None, alias="to", description="Date de fin (ISO 8601)"),
    async_mode: bool = Query(False, description="Lancer en mode asynchrone (par lots)"),
):
    """
    Synchronise les logs d'état Bolt depuis l'API Bolt vers la base de données locale.
    Si async_mode=True, lance la synchronisation en arrière-plan par lots.
    """
    try:
        if async_mode:
            # Mode asynchrone : lance en arrière-plan par lots
            sync_bolt_heavy_data_async(org_id=current_user["org_id"], company_id=company_id)
            return {
                "status": "success",
                "message": "State logs synchronization started in background (batched)",
                "mode": "async",
            }
        else:
            # Mode synchrone : synchronise immédiatement
            if not from_date:
                from_date = datetime.utcnow() - timedelta(days=30)
            if not to_date:
                to_date = datetime.utcnow()
            
            sync_state_logs(db, BoltClient(), company_id=company_id, start=from_date, end=to_date, org_id=current_user["org_id"])
            from app.models.bolt_state_log import BoltStateLog
            total = db.query(BoltStateLog).filter(BoltStateLog.org_id == current_user["org_id"]).count()
            return {
                "status": "success",
                "message": "State logs synchronized",
                "total_state_logs_in_db": total,
                "org_id_used": current_user["org_id"],
                "mode": "sync",
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/sync/orders/async")
def sync_bolt_orders_async(
    current_user: dict = Depends(get_current_user),
    company_id: str | None = Query(None, description="Company ID Bolt (optionnel)"),
    days_back: int = Query(30, description="Nombre de jours en arrière à synchroniser"),
):
    """
    Lance la synchronisation des orders en mode asynchrone par lots.
    Ne bloque pas le serveur.
    """
    try:
        sync_bolt_heavy_data_async(org_id=current_user["org_id"], company_id=company_id)
        return {
            "status": "success",
            "message": "Orders synchronization started in background (batched)",
            "days_back": days_back,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

