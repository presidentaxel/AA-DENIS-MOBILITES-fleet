from app.core.config import get_settings
from app.core.supabase_db import SupabaseDB
from app.models.heetch_driver import HeetchDriver
from app.heetch_integration.heetch_client import HeetchClient

settings = get_settings()


def sync_drivers_from_earnings(db: SupabaseDB, client: HeetchClient, org_id: str | None = None) -> None:
    """
    Synchronise les drivers Heetch depuis les données earnings.
    Les drivers sont extraits de la réponse de l'API earnings.
    
    Args:
        db: Instance de la base de données
        client: Client Heetch
        org_id: ID de l'organisation (utilise la config si non fourni)
    """
    from app.core import logging as app_logging
    from datetime import date, timedelta
    
    logger = app_logging.get_logger(__name__)
    
    # Déterminer org_id si non fourni
    if not org_id:
        org_id = settings.uber_default_org_id or "default_org"
    
    logger.info(f"[SYNC HEETCH DRIVERS] Début synchronisation depuis earnings (org_id={org_id})")
    
    try:
        # Récupérer les earnings de la semaine en cours pour extraire les drivers
        today = date.today()
        # Trouver le lundi de la semaine en cours
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)
        
        # Récupérer les earnings de cette semaine
        earnings_data = client.get_earnings(monday, period="weekly")
        
        drivers_data = earnings_data.get("drivers", [])
        logger.info(f"[SYNC HEETCH DRIVERS] {len(drivers_data)} drivers trouvés dans les earnings")
        
        saved_count = 0
        for driver_data in drivers_data:
            email = driver_data.get("email")
            if not email:
                logger.warning(f"[SYNC HEETCH DRIVERS] Driver sans email ignoré: {driver_data}")
                continue
            
            driver = HeetchDriver(
                id=email,  # Utiliser email comme ID
                org_id=org_id,
                first_name=driver_data.get("first_name", ""),
                last_name=driver_data.get("last_name", ""),
                email=email,
                image_url=driver_data.get("image_url"),
                active=True,  # Par défaut actif
            )
            
            db.merge(driver)
            saved_count += 1
        
        db.commit()
        logger.info(f"[SYNC HEETCH DRIVERS] {saved_count} drivers sauvegardés")
        
    except Exception as e:
        db.rollback()
        logger.error(f"[SYNC HEETCH DRIVERS] Erreur lors de la synchronisation: {e}", exc_info=True)
        raise

