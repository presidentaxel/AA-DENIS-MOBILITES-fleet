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
    
    payload = {
        "offset": offset,
        "limit": min(limit, 1000) if limit > 0 else 1000,  # Max 1000 selon la doc, défaut à 1000
        "company_id": int(company_id),
        "start_ts": thirty_days_ago,  # Timestamp de début (30 jours dans le passé, plage max autorisée)
        "end_ts": now,  # Timestamp de fin (maintenant)
        # portal_status omis car optionnel
        # search omis car optionnel et pas de recherche à effectuer
    }
    
    logger.info(f"Sync Bolt drivers: company_id={company_id}, limit={limit}, offset={offset}")
    logger.debug(f"Payload: {payload}")
    
    # Logs supplémentaires pour debug
    print(f"[SYNC DRIVERS] ===== SYNC DRIVERS CALL =====")
    print(f"[SYNC DRIVERS] company_id: {company_id} (type: {type(company_id)})")
    print(f"[SYNC DRIVERS] limit: {limit}, offset: {offset}")
    print(f"[SYNC DRIVERS] payload: {payload}")
    print(f"[SYNC DRIVERS] endpoint: /fleetIntegration/v1/getDrivers")
    print(f"[SYNC DRIVERS] ============================")
    
    # Appel POST vers l'endpoint Bolt
    data = client.post("/fleetIntegration/v1/getDrivers", payload)
    
    # La réponse Bolt a la structure: { "code": 0, "message": "...", "data": { "drivers": [...] } }
    if data.get("code") != 0:
        error_msg = data.get("message", "Unknown error")
        raise RuntimeError(f"Bolt API error: {error_msg}")
    
    drivers = data.get("data", {}).get("drivers", [])
    logger.info(f"Récupéré {len(drivers)} drivers depuis Bolt")
    
    if not drivers:
        logger.warning("Aucun driver récupéré depuis Bolt. Vérifie que company_id est correct.")
        return
    
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
        
        # Flush pour envoyer les changements à la DB sans commit
        db.flush()
        logger.info(f"{saved_count} drivers flushés (prêts à être commités)")
        
        # Commit explicite avec gestion d'erreur
        db.commit()
        logger.info(f"{saved_count} drivers commités avec org_id={org_id}")
        
        # Vérification après commit avec une nouvelle requête pour forcer la lecture depuis la DB
        db.expire_all()  # Expirer tous les objets de la session pour forcer une nouvelle lecture
        verify_count = db.query(BoltDriver).filter(BoltDriver.org_id == org_id).count()
        logger.info(f"Vérification après commit: {verify_count} drivers trouvés dans la DB avec org_id={org_id}")
        
        if verify_count == 0 and saved_count > 0:
            logger.error(f"ATTENTION: {saved_count} drivers devraient être sauvegardés mais aucun trouvé dans la DB!")
            logger.error(f"Vérifie que la connexion DB est correcte et que org_id={org_id} correspond à tes données")
            logger.error(f"URL DB (masquée): {config.database_url.replace(config.db_password, '***')}")
            
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur lors de la sauvegarde des drivers: {e}", exc_info=True)
        raise

