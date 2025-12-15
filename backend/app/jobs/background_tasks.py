"""
Système de tâches en arrière-plan pour synchronisations lourdes par lots.
Utilise threading pour éviter de bloquer le serveur.
"""
import asyncio
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from app.core.config import get_settings
from app.core.supabase_db import SupabaseDB
from app.core.supabase_client import get_supabase_client
from app.bolt_integration.services_trips import sync_trips
from app.bolt_integration.services_state_logs import sync_state_logs
from app.core import logging as app_logging

logger = app_logging.get_logger(__name__)
settings = get_settings()

# ThreadPoolExecutor pour les tâches en arrière-plan
executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="bolt_sync")


def sync_orders_in_batches(
    org_id: str,
    company_id: Optional[str] = None,
    days_back: int = 30,
    batch_size_days: int = 7,
    max_workers: int = 1
) -> dict:
    """
    Synchronise les orders par lots pour éviter de bloquer le serveur.
    
    Args:
        org_id: ID de l'organisation
        company_id: Company ID Bolt
        days_back: Nombre de jours en arrière à synchroniser
        batch_size_days: Nombre de jours par batch
        max_workers: Nombre de workers parallèles (1 = séquentiel pour éviter surcharge API)
    
    Returns:
        dict avec le statut de la synchronisation
    """
    logger.info(f"[BATCH SYNC ORDERS] Début synchronisation par lots pour org_id={org_id}")
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    
    # Diviser en batches de batch_size_days jours
    batches = []
    current_date = start_date
    while current_date < end_date:
        batch_end = min(current_date + timedelta(days=batch_size_days), end_date)
        batches.append((current_date, batch_end))
        current_date = batch_end
    
    logger.info(f"[BATCH SYNC ORDERS] {len(batches)} batches à traiter ({batch_size_days} jours par batch)")
    
    from app.bolt_integration.bolt_client import BoltClient
    supabase_client = get_supabase_client()
    db = SupabaseDB(supabase_client)
    client = BoltClient()
    
    total_saved = 0
    total_skipped = 0
    errors = []
    
    for i, (batch_start, batch_end) in enumerate(batches, 1):
        try:
            logger.info(f"[BATCH SYNC ORDERS] Batch {i}/{len(batches)}: {batch_start.date()} -> {batch_end.date()}")
            sync_trips(
                db=db,
                client=client,
                company_id=company_id,
                start=batch_start,
                end=batch_end,
                org_id=org_id,
                limit=1000,
                offset=0,
                incremental=False  # En batch, on synchronise la période spécifiée
            )
            logger.info(f"[BATCH SYNC ORDERS] ✓ Batch {i}/{len(batches)} terminé")
        except Exception as e:
            error_msg = f"Erreur batch {i}: {str(e)}"
            logger.error(f"[BATCH SYNC ORDERS] ✗ {error_msg}")
            errors.append(error_msg)
    
    # Compter le total final
    from app.models.bolt_order import BoltOrder
    total_in_db = db.query(BoltOrder).filter(BoltOrder.org_id == org_id).count()
    
    result = {
        "status": "success" if not errors else "partial",
        "batches_processed": len(batches),
        "errors": errors,
        "total_orders_in_db": total_in_db,
    }
    
    logger.info(f"[BATCH SYNC ORDERS] Synchronisation terminée: {result}")
    return result


def sync_state_logs_in_batches(
    org_id: str,
    company_id: Optional[str] = None,
    days_back: int = 30,
    batch_size_days: int = 7,
) -> dict:
    """
    Synchronise les state logs par lots pour éviter de bloquer le serveur.
    
    Args:
        org_id: ID de l'organisation
        company_id: Company ID Bolt
        days_back: Nombre de jours en arrière à synchroniser
        batch_size_days: Nombre de jours par batch
    
    Returns:
        dict avec le statut de la synchronisation
    """
    logger.info(f"[BATCH SYNC STATE LOGS] Début synchronisation par lots pour org_id={org_id}")
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    
    # Diviser en batches de batch_size_days jours
    batches = []
    current_date = start_date
    while current_date < end_date:
        batch_end = min(current_date + timedelta(days=batch_size_days), end_date)
        batches.append((current_date, batch_end))
        current_date = batch_end
    
    logger.info(f"[BATCH SYNC STATE LOGS] {len(batches)} batches à traiter ({batch_size_days} jours par batch)")
    
    from app.bolt_integration.bolt_client import BoltClient
    supabase_client = get_supabase_client()
    db = SupabaseDB(supabase_client)
    client = BoltClient()
    
    total_saved = 0
    total_skipped = 0
    errors = []
    
    for i, (batch_start, batch_end) in enumerate(batches, 1):
        try:
            logger.info(f"[BATCH SYNC STATE LOGS] Batch {i}/{len(batches)}: {batch_start.date()} -> {batch_end.date()}")
            sync_state_logs(
                db=db,
                client=client,
                company_id=company_id,
                start=batch_start,
                end=batch_end,
                org_id=org_id,
                limit=1000,
                offset=0,
                incremental=False  # En batch, on synchronise la période spécifiée
            )
            logger.info(f"[BATCH SYNC STATE LOGS] ✓ Batch {i}/{len(batches)} terminé")
        except Exception as e:
            error_msg = f"Erreur batch {i}: {str(e)}"
            logger.error(f"[BATCH SYNC STATE LOGS] ✗ {error_msg}")
            errors.append(error_msg)
    
    # Compter le total final
    from app.models.bolt_state_log import BoltStateLog
    total_in_db = db.query(BoltStateLog).filter(BoltStateLog.org_id == org_id).count()
    
    result = {
        "status": "success" if not errors else "partial",
        "batches_processed": len(batches),
        "errors": errors,
        "total_state_logs_in_db": total_in_db,
    }
    
    logger.info(f"[BATCH SYNC STATE LOGS] Synchronisation terminée: {result}")
    return result


def sync_bolt_heavy_data_async(org_id: str, company_id: Optional[str] = None) -> None:
    """
    Lance la synchronisation des données lourdes (orders et state_logs) en arrière-plan.
    Ne bloque pas le serveur.
    """
    logger.info(f"[ASYNC SYNC] Lancement synchronisation asynchrone pour org_id={org_id}")
    
    def run_sync():
        try:
            # Synchroniser orders par lots
            sync_orders_in_batches(
                org_id=org_id,
                company_id=company_id,
                days_back=30,
                batch_size_days=7
            )
            
            # Synchroniser state logs par lots
            sync_state_logs_in_batches(
                org_id=org_id,
                company_id=company_id,
                days_back=30,
                batch_size_days=7
            )
            
            logger.info(f"[ASYNC SYNC] Synchronisation asynchrone terminée pour org_id={org_id}")
        except Exception as e:
            logger.error(f"[ASYNC SYNC] Erreur lors de la synchronisation asynchrone: {str(e)}", exc_info=True)
    
    # Lancer dans le ThreadPoolExecutor
    executor.submit(run_sync)
    logger.info(f"[ASYNC SYNC] Tâche soumise au pool d'exécution pour org_id={org_id}")

