import time

from app.core.config import get_settings
from app.core.supabase_db import SupabaseDB
from app.models.bolt_vehicle import BoltVehicle
from app.models.bolt_org import BoltOrganization
from app.bolt_integration.bolt_client import BoltClient

settings = get_settings()


def sync_vehicles(db: SupabaseDB, client: BoltClient, company_id: str | None = None, org_id: str | None = None, limit: int = 100, offset: int = 0) -> None:
    """
    Synchronise les véhicules Bolt depuis l'API.
    Utilise POST /fleetIntegration/v1/getVehicles selon la documentation Bolt.
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
    
    # IMPORTANT: company_id est REQUIS par l'API Bolt
    if not company_id or (company_id and not company_id.isdigit()):
        raise ValueError(
            "BOLT_DEFAULT_FLEET_ID (company_id) est requis pour synchroniser les véhicules Bolt. "
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
        "limit": min(limit, 100) if limit > 0 else 100,  # Max 100 selon la doc, défaut à 100
        "company_id": int(company_id),
        "start_ts": thirty_days_ago,  # Timestamp de début (30 jours dans le passé, plage max autorisée)
        "end_ts": now,  # Timestamp de fin (maintenant)
        # portal_status omis car optionnel
        # search omis car optionnel et pas de recherche à effectuer
    }
    
    logger.info(f"Sync Bolt vehicles: company_id={company_id}, limit={limit}, offset={offset}")
    logger.debug(f"Payload: {payload}")
    
    # Appel POST vers l'endpoint Bolt
    data = client.post("/fleetIntegration/v1/getVehicles", payload)
    
    if data.get("code") != 0:
        error_msg = data.get("message", "Unknown error")
        raise RuntimeError(f"Bolt API error: {error_msg}")
    
    # La réponse Bolt a la structure: { "code": 0, "message": "...", "data": { "vehicles": [...] } }
    vehicles = data.get("data", {}).get("vehicles", [])
    logger.info(f"Récupéré {len(vehicles)} véhicules depuis Bolt")
    
    if not vehicles:
        logger.warning("Aucun véhicule récupéré depuis Bolt. Vérifie que company_id est correct.")
        return
    
    org_id = settings.bolt_default_fleet_id or settings.uber_default_org_id or "default_org"
    saved_count = 0
    
    for v in vehicles:
        vehicle_uuid = v.get("uuid") or v.get("id")
        if not vehicle_uuid:
            logger.warning(f"Véhicule sans UUID ignoré: {v}")
            continue
            
        db.merge(
            BoltVehicle(
                id=vehicle_uuid,
                org_id=org_id,
                plate=v.get("reg_number", ""),  # Bolt utilise "reg_number"
                model=v.get("model"),
                provider_vehicle_id=vehicle_uuid,
            )
        )
        saved_count += 1
    
    db.commit()
    logger.info(f"{saved_count} véhicules sauvegardés avec org_id={org_id}")

