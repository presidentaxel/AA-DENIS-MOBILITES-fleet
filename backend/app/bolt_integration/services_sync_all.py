"""
Service d'orchestration pour synchroniser toutes les données Bolt dans le bon ordre.
"""
from datetime import datetime, timedelta

from app.core.config import get_settings
from app.core import logging as app_logging
from app.core.supabase_db import SupabaseDB
from app.bolt_integration.bolt_client import BoltClient
from app.bolt_integration.services_orgs import sync_orgs
from app.bolt_integration.services_drivers import sync_drivers
from app.bolt_integration.services_vehicles import sync_vehicles
from app.bolt_integration.services_trips import sync_trips
from app.bolt_integration.services_state_logs import sync_state_logs
from app.models.bolt_driver import BoltDriver
from app.models.bolt_order import BoltOrder

settings = get_settings()
logger = app_logging.get_logger(__name__)


def sync_all_bolt_data(db: SupabaseDB, org_id: str, company_id: str | None = None) -> dict:
    """
    Synchronise toutes les données Bolt dans l'ordre :
    1. Organizations (company_ids)
    2. Drivers
    3. Vehicles
    4. Orders (commandes/trips depuis getFleetOrders)
    5. State Logs (logs d'état depuis getFleetStateLogs)
    
    Args:
        db: Instance de SupabaseDB
        org_id: ID de l'organisation
        company_id: Company ID Bolt (optionnel)
    
    Returns:
        dict avec le statut de chaque synchronisation
    """
    results = {
        "orgs": {"status": "pending", "error": None},
        "drivers": {"status": "pending", "error": None, "count": 0},
        "vehicles": {"status": "pending", "error": None, "count": 0},
        "orders": {"status": "pending", "error": None, "count": 0},
        "state_logs": {"status": "pending", "error": None, "count": 0},
    }
    
    client = BoltClient()
    
    try:
        # 1. Synchroniser les organizations
        logger.info(f"[SYNC ALL] Début synchronisation Bolt pour org_id={org_id}")
        logger.info("[SYNC ALL] Étape 1/5: Synchronisation des organizations...")
        try:
            sync_orgs(db, client, org_id=org_id)
            results["orgs"]["status"] = "success"
            logger.info("[SYNC ALL] ✓ Organizations synchronisées")
        except Exception as e:
            logger.error(f"[SYNC ALL] ✗ Erreur sync organizations: {str(e)}")
            results["orgs"]["status"] = "error"
            results["orgs"]["error"] = str(e)
            # On continue quand même
        
        # 2. Synchroniser les drivers
        logger.info("[SYNC ALL] Étape 2/5: Synchronisation des drivers...")
        try:
            sync_drivers(db, client, company_id=company_id, org_id=org_id)
            # Compter les drivers synchronisés
            driver_count = db.query(BoltDriver).filter(BoltDriver.org_id == org_id).count()
            results["drivers"]["status"] = "success"
            results["drivers"]["count"] = driver_count
            logger.info(f"[SYNC ALL] ✓ Drivers synchronisés: {driver_count} drivers")
        except Exception as e:
            logger.error(f"[SYNC ALL] ✗ Erreur sync drivers: {str(e)}")
            results["drivers"]["status"] = "error"
            results["drivers"]["error"] = str(e)
            # Si on ne peut pas sync les drivers, on ne peut pas sync trips/earnings
            return results
        
        # 3. Synchroniser les véhicules
        logger.info("[SYNC ALL] Étape 3/5: Synchronisation des véhicules...")
        try:
            from app.models.bolt_vehicle import BoltVehicle
            sync_vehicles(db, client, company_id=company_id, org_id=org_id)
            vehicle_count = db.query(BoltVehicle).filter(BoltVehicle.org_id == org_id).count()
            results["vehicles"]["status"] = "success"
            results["vehicles"]["count"] = vehicle_count
            logger.info(f"[SYNC ALL] ✓ Véhicules synchronisés: {vehicle_count} véhicules")
        except Exception as e:
            logger.error(f"[SYNC ALL] ✗ Erreur sync véhicules: {str(e)}")
            results["vehicles"]["status"] = "error"
            results["vehicles"]["error"] = str(e)
            # On continue pour sync trips/earnings
        
        # 4. Synchroniser les orders (commandes/trips)
        logger.info("[SYNC ALL] Étape 4/5: Synchronisation des orders...")
        try:
            # Par défaut, sync les 30 derniers jours
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            
            # Sync orders pour la company (mode incrémental activé par défaut)
            sync_trips(db, client, company_id=company_id, start=start_date, end=end_date, org_id=org_id, incremental=True)
            
            # Compter les orders synchronisés
            orders_count = db.query(BoltOrder).filter(BoltOrder.org_id == org_id).count()
            results["orders"]["status"] = "success"
            results["orders"]["count"] = orders_count
            logger.info(f"[SYNC ALL] ✓ Orders synchronisés: {orders_count} orders")
        except Exception as e:
            logger.error(f"[SYNC ALL] ✗ Erreur sync orders: {str(e)}")
            results["orders"]["status"] = "error"
            results["orders"]["error"] = str(e)
        
        # 5. Synchroniser les state logs
        logger.info("[SYNC ALL] Étape 5/5: Synchronisation des state logs...")
        try:
            # Par défaut, sync les 30 derniers jours
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            
            # Sync state logs pour la company (mode incrémental activé par défaut)
            sync_state_logs(db, client, company_id=company_id, start=start_date, end=end_date, org_id=org_id, incremental=True)
            
            from app.models.bolt_state_log import BoltStateLog
            state_logs_count = db.query(BoltStateLog).filter(BoltStateLog.org_id == org_id).count()
            results["state_logs"]["status"] = "success"
            results["state_logs"]["count"] = state_logs_count
            logger.info(f"[SYNC ALL] ✓ State logs synchronisés: {state_logs_count} logs")
        except Exception as e:
            logger.error(f"[SYNC ALL] ✗ Erreur sync state logs: {str(e)}")
            results["state_logs"]["status"] = "error"
            results["state_logs"]["error"] = str(e)
        
        logger.info(f"[SYNC ALL] Synchronisation complète pour org_id={org_id}")
        return results
        
    except Exception as e:
        logger.error(f"[SYNC ALL] Erreur générale: {str(e)}")
        results["error"] = str(e)
        return results

