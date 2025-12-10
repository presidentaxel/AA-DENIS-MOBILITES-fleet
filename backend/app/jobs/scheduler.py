from apscheduler.schedulers.background import BackgroundScheduler

from app.jobs import job_sync_drivers, job_sync_metrics, job_sync_orgs, job_sync_payments, job_sync_vehicles
from app.jobs import job_sync_bolt_drivers, job_sync_bolt_vehicles, job_sync_bolt_trips, job_sync_bolt_earnings


def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(job_sync_orgs.run, "cron", hour=3)
    scheduler.add_job(job_sync_drivers.run, "cron", hour="*/6")
    scheduler.add_job(job_sync_vehicles.run, "cron", hour="*/6")
    scheduler.add_job(job_sync_metrics.run, "cron", hour="*/12")
    scheduler.add_job(job_sync_payments.run, "cron", minute="*/30")
    scheduler.add_job(job_sync_bolt_drivers.run, "cron", minute="*/15")
    scheduler.add_job(job_sync_bolt_vehicles.run, "cron", minute="*/15")
    scheduler.add_job(job_sync_bolt_trips.run, "cron", hour="*/6")
    scheduler.add_job(job_sync_bolt_earnings.run, "cron", hour="*/1")
    return scheduler

