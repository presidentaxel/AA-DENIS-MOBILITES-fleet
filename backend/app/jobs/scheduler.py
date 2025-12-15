from apscheduler.schedulers.background import BackgroundScheduler

from app.jobs import job_sync_drivers, job_sync_metrics, job_sync_orgs, job_sync_payments, job_sync_vehicles
from app.jobs import job_sync_bolt_drivers, job_sync_bolt_vehicles
from app.jobs.background_tasks import sync_bolt_heavy_data_async
from app.core.config import get_settings

settings = get_settings()


def create_scheduler() -> BackgroundScheduler:
    """
    Crée le scheduler pour les tâches périodiques.
    Les données lourdes (orders, state_logs) sont synchronisées une fois par jour en arrière-plan.
    """
    scheduler = BackgroundScheduler(timezone="UTC")
    
    # Synchronisations Uber (gardées comme avant)
    scheduler.add_job(job_sync_orgs.run, "cron", hour=3)
    scheduler.add_job(job_sync_drivers.run, "cron", hour="*/6")
    scheduler.add_job(job_sync_vehicles.run, "cron", hour="*/6")
    scheduler.add_job(job_sync_metrics.run, "cron", hour="*/12")
    scheduler.add_job(job_sync_payments.run, "cron", minute="*/30")
    
    # Synchronisations Bolt légères (drivers, vehicles) - fréquentes
    scheduler.add_job(job_sync_bolt_drivers.run, "cron", hour="*/6")  # Toutes les 6h
    scheduler.add_job(job_sync_bolt_vehicles.run, "cron", hour="*/6")  # Toutes les 6h
    
    # Synchronisations Bolt lourdes (orders, state_logs) - une fois par jour, en arrière-plan
    # Exécution à 2h du matin pour éviter la charge
    def sync_heavy_data():
        org_id = settings.uber_default_org_id or "default_org"
        sync_bolt_heavy_data_async(org_id=org_id)
    
    scheduler.add_job(sync_heavy_data, "cron", hour=2, minute=0)
    
    return scheduler

