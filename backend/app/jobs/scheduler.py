from apscheduler.schedulers.background import BackgroundScheduler

from app.jobs import job_sync_drivers, job_sync_metrics, job_sync_orgs, job_sync_payments, job_sync_vehicles
from app.jobs import job_sync_bolt_drivers, job_sync_bolt_vehicles
from app.jobs.background_tasks import sync_bolt_heavy_data_async
from app.core.config import get_settings

settings = get_settings()


def sync_state_logs_incremental():
    """
    Synchronise rapidement les state logs en mode incrémental (seulement les nouveaux logs).
    Cette fonction est appelée fréquemment pour maintenir les logs à jour.
    """
    from app.core.supabase_db import get_supabase_client, SupabaseDB
    from app.bolt_integration.bolt_client import BoltClient
    from app.bolt_integration.services_state_logs import sync_state_logs
    from app.core import logging as app_logging
    
    logger = app_logging.get_logger(__name__)
    org_id = settings.uber_default_org_id or "default_org"
    
    try:
        logger.info(f"[INCREMENTAL STATE LOGS SYNC] Début synchronisation incrémentale pour org_id={org_id}")
        supabase_client = get_supabase_client()
        db = SupabaseDB(supabase_client)
        client = BoltClient()
        
        # Mode incrémental : récupère seulement les nouveaux logs depuis le dernier sync
        sync_state_logs(db, client, org_id=org_id, incremental=True)
        
        logger.info(f"[INCREMENTAL STATE LOGS SYNC] Synchronisation incrémentale terminée pour org_id={org_id}")
    except Exception as e:
        logger.error(f"[INCREMENTAL STATE LOGS SYNC] Erreur lors de la synchronisation incrémentale: {str(e)}", exc_info=True)


def create_scheduler() -> BackgroundScheduler:
    """
    Crée le scheduler pour les tâches périodiques.
    Les données lourdes (orders, state_logs) sont synchronisées une fois par jour en arrière-plan.
    Les state logs sont également synchronisés fréquemment en mode incrémental pour maintenir les données à jour.
    """
    scheduler = BackgroundScheduler(timezone="UTC")
    
    # Synchronisations Uber - DÉSACTIVÉES TEMPORAIREMENT
    # Les autorisations Uber ne sont pas encore configurées, désactivation pour éviter les erreurs 400
    # scheduler.add_job(job_sync_orgs.run, "cron", hour=3)
    # scheduler.add_job(job_sync_drivers.run, "cron", hour="*/6")
    # scheduler.add_job(job_sync_vehicles.run, "cron", hour="*/6")
    # scheduler.add_job(job_sync_metrics.run, "cron", hour="*/12")
    # scheduler.add_job(job_sync_payments.run, "cron", minute="*/30")
    
    # Synchronisations Bolt légères (drivers, vehicles) - fréquentes
    scheduler.add_job(job_sync_bolt_drivers.run, "cron", hour="*/6")  # Toutes les 6h
    scheduler.add_job(job_sync_bolt_vehicles.run, "cron", hour="*/6")  # Toutes les 6h
    
    # Synchronisation rapide des state logs en mode incrémental - toutes les heures
    # Cela maintient les logs à jour sans surcharger l'API (seulement les nouveaux logs)
    scheduler.add_job(sync_state_logs_incremental, "cron", minute=0)  # Toutes les heures à :00
    
    # Synchronisations Bolt lourdes (orders, state_logs complets) - une fois par jour, en arrière-plan
    # Exécution à 2h du matin pour éviter la charge
    def sync_heavy_data():
        org_id = settings.uber_default_org_id or "default_org"
        sync_bolt_heavy_data_async(org_id=org_id)
    
    scheduler.add_job(sync_heavy_data, "cron", hour=2, minute=0)
    
    return scheduler

