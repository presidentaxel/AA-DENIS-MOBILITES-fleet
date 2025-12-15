from datetime import datetime

from app.core.config import get_settings
from app.core.supabase_db import SupabaseDB
from app.models.bolt_earning import BoltEarning
from app.bolt_integration.bolt_client import BoltClient

settings = get_settings()


def sync_earnings(db: SupabaseDB, client: BoltClient, driver_id: str | None = None, start: datetime | None = None, end: datetime | None = None, org_id: str | None = None) -> None:
    """
    Synchronise les revenus Bolt depuis l'API.
    NOTE: L'endpoint exact pour les earnings n'est pas encore documenté dans l'API Bolt Fleet Integration.
    Cette fonction est désactivée jusqu'à ce que l'endpoint correct soit identifié.
    """
    from app.core import logging as app_logging
    logger = app_logging.get_logger(__name__)
    
    logger.warning("sync_earnings: Endpoint /earnings non disponible dans l'API Bolt Fleet Integration. Synchronisation désactivée.")
    return
    
    # Code désactivé - à réactiver une fois l'endpoint correct identifié
    # # Déterminer org_id si non fourni
    # if not org_id:
    #     org_id = settings.bolt_default_fleet_id or settings.uber_default_org_id or "default_org"
    # 
    # # TODO: Utiliser le bon endpoint Bolt Fleet Integration (probablement /fleetIntegration/v1/getEarnings)
    # # Pour l'instant, on essaie avec l'endpoint standard
    # params = {}
    # if driver_id:
    #     params["driver_id"] = driver_id
    # if start:
    #     params["from"] = start.isoformat()
    # if end:
    #     params["to"] = end.isoformat()
    # data = client.get("/fleetIntegration/v1/getEarnings", params=params)
    # earnings = data.get("data", [])
    # for e in earnings:
    #     db.merge(
    #         BoltEarning(
    #             id=e["id"],
    #             org_id=org_id,
    #             driver_id=e.get("driver_id"),
    #             payout_date=datetime.fromisoformat(e["payout_date"]),
    #             amount=e.get("amount", 0),
    #             type=e.get("type"),
    #             currency=e.get("currency", "EUR"),
    #         )
    #     )
    # db.commit()

