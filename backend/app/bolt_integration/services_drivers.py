import time

from app.core.config import get_settings
from app.core.supabase_db import SupabaseDB
from app.models.bolt_driver import BoltDriver
from app.models.bolt_org import BoltOrganization
from app.bolt_integration.bolt_client import BoltClient

settings = get_settings()


def sync_drivers(db: SupabaseDB, client: BoltClient, company_id: str | None = None, org_id: str | None = None, limit: int = 1000, offset: int = 0) -> None:
    """
    Synchronise les chauffeurs Bolt depuis l'API.
    Utilise POST /fleetIntegration/v1/getDrivers selon la documentation Bolt.
    Gère la pagination automatiquement pour récupérer TOUS les drivers.
    """
    from app.core.config import get_settings
    from app.core import logging as app_logging
    
    logger = app_logging.get_logger(__name__)
    config = get_settings()
    
    # Déterminer org_id si non fourni
    if not org_id:
        org_id = config.bolt_default_fleet_id or config.uber_default_org_id or "default_org"
    
    # Utiliser company_id depuis les paramètres, puis depuis la DB, puis depuis les settings
    if not company_id:
        # Essayer de récupérer depuis la DB
        bolt_org = db.query(BoltOrganization).filter(BoltOrganization.org_id == org_id).first()
        if bolt_org:
            company_id = bolt_org.id
            logger.info(f"Utilisation du company_id depuis la DB: {company_id}")
        else:
            # Fallback sur les settings
            company_id = config.bolt_default_fleet_id
    
    # Construire le body selon la documentation Bolt
    # IMPORTANT: company_id est REQUIS par l'API Bolt, ne peut pas être 0
    if not company_id or (company_id and not company_id.isdigit()):
        raise ValueError(
            "BOLT_DEFAULT_FLEET_ID (company_id) est requis pour synchroniser les drivers Bolt. "
            "Ajoute-le dans backend/.env avec la valeur de ton company_id Bolt."
        )
    
    # Construire le payload selon la documentation Bolt
    # Format exact de la doc: offset, limit, company_id, start_ts, end_ts, portal_status, search
    # Note: L'API exige start_ts et end_ts même si la doc dit qu'ils sont optionnels
    # La plage de dates doit être strictement inférieure à 31 jours (sinon erreur INVALID_DATE_RANGE)
    # start_ts peut remonter jusqu'à 16 mois dans le passé, mais la plage max est 30 jours
    # On utilise 30 jours dans le passé pour start_ts et maintenant pour end_ts
    now = int(time.time())
    # 30 jours = 30 * 24 * 60 * 60 secondes = 2,592,000 secondes
    thirty_days_ago = now - (30 * 24 * 60 * 60)
    
    # Pagination : récupérer tous les drivers
    batch_limit = min(limit, 1000) if limit > 0 else 1000  # Max 1000 selon la doc
    current_offset = offset
    total_saved = 0
    page = 1
    
    logger.info(f"[SYNC DRIVERS] Début synchronisation complète des drivers (company_id={company_id}, org_id={org_id})")
    
    while True:
        payload = {
            "offset": current_offset,
            "limit": batch_limit,
            "company_id": int(company_id),
            "start_ts": thirty_days_ago,
            "end_ts": now,
        }
        
        logger.info(f"[SYNC DRIVERS] Page {page}: offset={current_offset}, limit={batch_limit}")
        
        # Appel POST vers l'endpoint Bolt
        data = client.post("/fleetIntegration/v1/getDrivers", payload)
        
        # La réponse Bolt a la structure: { "code": 0, "message": "...", "data": { "drivers": [...] } }
        if data.get("code") != 0:
            error_msg = data.get("message", "Unknown error")
            raise RuntimeError(f"Bolt API error: {error_msg}")
        
        drivers = data.get("data", {}).get("drivers", [])
        logger.info(f"[SYNC DRIVERS] Page {page}: Récupéré {len(drivers)} drivers depuis Bolt")
        
        if not drivers:
            # Plus de drivers à récupérer
            logger.info(f"[SYNC DRIVERS] Aucun driver supplémentaire, fin de la pagination")
            break
        
        # Sauvegarder les drivers de cette page
        saved_count = 0
        try:
            for d in drivers:
                # Mapper les champs Bolt vers notre modèle
                driver_uuid = d.get("driver_uuid") or d.get("id")
                if not driver_uuid:
                    logger.warning(f"Driver sans UUID ignoré: {d}")
                    continue
                    
                driver = BoltDriver(
                    id=driver_uuid,
                    org_id=org_id,
                    first_name=d.get("first_name", ""),
                    last_name=d.get("last_name", ""),
                    email=d.get("email"),
                    phone=d.get("phone"),
                    active=d.get("state") == "active" if d.get("state") else True,
                )
                
                db.merge(driver)
                saved_count += 1
            
            # Commit après chaque page pour éviter de perdre les données en cas d'erreur
            db.commit()
            total_saved += saved_count
            logger.info(f"[SYNC DRIVERS] Page {page}: {saved_count} drivers sauvegardés (total: {total_saved})")
            
        except Exception as e:
            db.rollback()
            logger.error(f"[SYNC DRIVERS] Erreur lors de la sauvegarde de la page {page}: {e}", exc_info=True)
            raise
        
        # Si on a récupéré moins de drivers que le limit, c'est qu'on a atteint la fin
        if len(drivers) < batch_limit:
            logger.info(f"[SYNC DRIVERS] Dernière page atteinte ({len(drivers)} < {batch_limit})")
            break
        
        # Passer à la page suivante
        current_offset += batch_limit
        page += 1
        
        # Sécurité : éviter les boucles infinies (max 1000 pages = 1M drivers max)
        if page > 1000:
            logger.warning(f"[SYNC DRIVERS] Limite de sécurité atteinte (1000 pages), arrêt de la synchronisation")
            break
    
    # Vérification finale
    db.expire_all()
    verify_count = db.query(BoltDriver).filter(BoltDriver.org_id == org_id).count()
    logger.info(f"[SYNC DRIVERS] Synchronisation terminée: {total_saved} drivers sauvegardés, {verify_count} drivers dans la DB avec org_id={org_id}")
    
    if verify_count == 0 and total_saved > 0:
        logger.error(f"[SYNC DRIVERS] ATTENTION: {total_saved} drivers devraient être sauvegardés mais aucun trouvé dans la DB!")
        logger.error(f"[SYNC DRIVERS] Vérifie que la connexion DB est correcte et que org_id={org_id} correspond à tes données")

