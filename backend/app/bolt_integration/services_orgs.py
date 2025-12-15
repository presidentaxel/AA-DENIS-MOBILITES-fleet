from app.core.config import get_settings
from app.core import logging as app_logging
from app.core.supabase_db import SupabaseDB
from app.models.bolt_org import BoltOrganization
from app.bolt_integration.bolt_client import BoltClient

settings = get_settings()
logger = app_logging.get_logger(__name__)


def sync_orgs(db: SupabaseDB, client: BoltClient, org_id: str | None = None) -> None:
    """
    Synchronise les organizations Bolt depuis l'API.
    Appelle /fleetIntegration/v1/getCompanies pour obtenir les company_ids disponibles.
    """
    if not org_id:
        org_id = settings.bolt_default_fleet_id or settings.uber_default_org_id or "default_org"
    
    logger.info(f"Sync Bolt organizations (company_ids)")
    
    try:
        # Appel GET vers l'endpoint getCompanies
        data = client.get("/fleetIntegration/v1/getCompanies")
        
        # La réponse Bolt a la structure: { "code": 0, "message": "OK", "data": { "company_ids": [...] } }
        if data.get("code") != 0:
            error_msg = data.get("message", "Unknown error")
            raise RuntimeError(f"Bolt API error: {error_msg}")
        
        company_ids = data.get("data", {}).get("company_ids", [])
        logger.info(f"Récupéré {len(company_ids)} company_id(s) depuis Bolt: {company_ids}")
        
        if not company_ids:
            logger.warning("Aucun company_id récupéré depuis Bolt")
            return
        
        # Sauvegarder chaque company_id dans la table bolt_organizations
        saved_count = 0
        for company_id in company_ids:
            company_id_str = str(company_id)
            db.merge(
                BoltOrganization(
                    id=company_id_str,
                    org_id=org_id,
                    name=f"Bolt Company {company_id_str}",  # Nom par défaut, peut être mis à jour plus tard
                )
            )
            saved_count += 1
        
        db.commit()
        logger.info(f"{saved_count} organization(s) Bolt sauvegardée(s) avec org_id={org_id}")
        
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation des organizations Bolt: {str(e)}")
        raise

