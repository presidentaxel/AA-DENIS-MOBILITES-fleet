import time
from datetime import datetime

from app.core.config import get_settings
from app.core.supabase_db import SupabaseDB
from app.models.bolt_state_log import BoltStateLog
from app.models.bolt_org import BoltOrganization
from app.bolt_integration.bolt_client import BoltClient

settings = get_settings()


def sync_state_logs(db: SupabaseDB, client: BoltClient, company_id: str | None = None, start: datetime | None = None, end: datetime | None = None, org_id: str | None = None, limit: int = 1000, offset: int = 0, incremental: bool = True) -> None:
    """
    Synchronise les logs d'état des drivers Bolt depuis l'API getFleetStateLogs.
    Utilise POST /fleetIntegration/v1/getFleetStateLogs selon la documentation Bolt.
    
    Args:
        incremental: Si True, récupère le dernier timestamp synchronisé et ne synchronise que les nouveaux logs.
                    Sinon, synchronise la période spécifiée.
    """
    from app.core import logging as app_logging
    logger = app_logging.get_logger(__name__)
    
    # Déterminer org_id si non fourni
    if not org_id:
        org_id = settings.bolt_default_fleet_id or settings.uber_default_org_id or "default_org"
    
    # Utiliser company_id depuis les paramètres, puis depuis la DB, puis depuis les settings
    if not company_id:
        # Essayer de récupérer depuis la DB
        bolt_org = db.query(BoltOrganization).filter(BoltOrganization.org_id == org_id).first()
        if bolt_org:
            company_id = bolt_org.id
            logger.info(f"Utilisation du company_id depuis la DB: {company_id}")
        else:
            # Fallback sur les settings
            company_id = settings.bolt_default_fleet_id
    
    if not company_id:
        raise ValueError("company_id est requis pour synchroniser les state logs Bolt")
    
    # Mode incrémental : récupérer le dernier timestamp synchronisé
    if incremental and not start:
        # Récupérer le dernier created timestamp pour cette org
        last_log = db.query(BoltStateLog).filter(
            BoltStateLog.org_id == org_id
        ).order_by(BoltStateLog.created.desc()).first()
        
        if last_log and last_log.created:
            # Commencer juste après le dernier log synchronisé
            start = datetime.fromtimestamp(last_log.created + 1)
            logger.info(f"[INCREMENTAL SYNC STATE LOGS] Dernier log synchronisé: {start.isoformat()}, reprise à partir de là")
        else:
            # Première sync : 30 jours en arrière
            start = datetime.fromtimestamp(time.time() - (30 * 24 * 60 * 60))
            logger.info(f"[INCREMENTAL SYNC STATE LOGS] Première sync, départ depuis 30 jours")
    elif not start:
        # Mode non-incrémental ou start explicitement fourni
        if not start:
            start = datetime.fromtimestamp(time.time() - (30 * 24 * 60 * 60))
    
    # Date de fin : maintenant par défaut
    if not end:
        end = datetime.utcnow()
    
    # Limite : ne jamais aller plus loin que 16 mois en arrière (limite API Bolt)
    max_days_back = 16 * 30  # ~16 mois
    earliest_allowed = datetime.fromtimestamp(time.time() - (max_days_back * 24 * 60 * 60))
    if start < earliest_allowed:
        logger.warning(f"[SYNC STATE LOGS] Date de début {start} trop ancienne, limitation à {earliest_allowed}")
        start = earliest_allowed
    
    start_ts = int(start.timestamp())
    end_ts = int(end.timestamp())
    
    # Pagination : récupérer tous les state logs
    batch_limit = min(limit, 1000) if limit > 0 else 1000  # Max 1000 selon la doc
    current_offset = offset
    total_saved = 0
    total_skipped = 0
    page = 1
    
    logger.info(f"[SYNC STATE LOGS] Début synchronisation complète des state logs (company_id={company_id}, org_id={org_id}, start_ts={start_ts}, end_ts={end_ts})")
    
    # Récupérer les IDs existants pour cette période une seule fois (pour éviter les doublons)
    existing_logs = db.query(BoltStateLog).filter(
        BoltStateLog.org_id == org_id,
        BoltStateLog.created >= start_ts,
        BoltStateLog.created <= end_ts
    ).all()
    existing_ids = {log.id for log in existing_logs}
    logger.info(f"[SYNC STATE LOGS] {len(existing_ids)} state logs déjà présents pour cette période")
    
    while True:
        # Construire le payload selon la documentation Bolt
        payload = {
            "company_id": int(company_id),
            "limit": batch_limit,
            "offset": current_offset,
            "start_ts": start_ts,
            "end_ts": end_ts,
        }
        
        logger.info(f"[SYNC STATE LOGS] Page {page}: offset={current_offset}, limit={batch_limit}")
        
        # Appel POST vers l'endpoint Bolt
        data = client.post("/fleetIntegration/v1/getFleetStateLogs", payload)
        
        # La réponse Bolt a la structure: { "code": 0, "message": "...", "data": { "state_logs": [...] } }
        if data.get("code") != 0:
            error_msg = data.get("message", "Unknown error")
            raise RuntimeError(f"Bolt API error: {error_msg}")
        
        state_logs_data = data.get("data", {})
        state_logs = state_logs_data.get("state_logs", [])
        logger.info(f"[SYNC STATE LOGS] Page {page}: Récupéré {len(state_logs)} state logs depuis Bolt")
        
        if not state_logs:
            # Plus de state logs à récupérer
            logger.info(f"[SYNC STATE LOGS] Aucun state log supplémentaire, fin de la pagination")
            break
        
        # Sauvegarder les state logs de cette page
        saved_count = 0
        skipped_count = 0
        
        try:
            for log in state_logs:
                # Générer un ID unique: driver_uuid + created timestamp
                log_id = f"{log.get('driver_uuid')}_{log.get('created')}"
                
                # Skip si déjà présent
                if log_id in existing_ids:
                    skipped_count += 1
                    continue
                
                # Ajouter à la liste des existants pour éviter les doublons dans les pages suivantes
                existing_ids.add(log_id)
                
                # Extraire active_categories (structure complexe)
                active_categories = log.get("active_categories")
                
                bolt_state_log = BoltStateLog(
                    id=log_id,
                    org_id=org_id,
                    driver_uuid=log.get("driver_uuid"),
                    vehicle_uuid=log.get("vehicle_uuid"),
                    created=log.get("created"),
                    state=log.get("state"),
                    lat=log.get("lat"),
                    lng=log.get("lng"),
                    active_categories=active_categories if active_categories else None,
                )
                
                db.merge(bolt_state_log)
                saved_count += 1
            
            # Commit après chaque page pour éviter de perdre les données en cas d'erreur
            db.commit()
            total_saved += saved_count
            total_skipped += skipped_count
            logger.info(f"[SYNC STATE LOGS] Page {page}: {saved_count} state logs sauvegardés, {skipped_count} ignorés (total: {total_saved} sauvegardés, {total_skipped} ignorés)")
            
        except Exception as e:
            db.rollback()
            logger.error(f"[SYNC STATE LOGS] Erreur lors de la sauvegarde de la page {page}: {e}", exc_info=True)
            raise
        
        # Si on a récupéré moins de state logs que le limit, c'est qu'on a atteint la fin
        if len(state_logs) < batch_limit:
            logger.info(f"[SYNC STATE LOGS] Dernière page atteinte ({len(state_logs)} < {batch_limit})")
            break
        
        # Passer à la page suivante
        current_offset += batch_limit
        page += 1
        
        # Sécurité : éviter les boucles infinies (max 1000 pages = 1M logs max)
        if page > 1000:
            logger.warning(f"[SYNC STATE LOGS] Limite de sécurité atteinte (1000 pages), arrêt de la synchronisation")
            break
    
    logger.info(f"[SYNC STATE LOGS] Synchronisation terminée: {total_saved} state logs sauvegardés, {total_skipped} déjà présents (ignorés) avec org_id={org_id}")

