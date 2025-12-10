from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.bolt_driver import BoltDriver
from app.bolt_integration.bolt_client import BoltClient

settings = get_settings()


def sync_drivers(db: Session, client: BoltClient, company_id: str | None = None, limit: int = 1000, offset: int = 0) -> None:
    """
    Synchronise les chauffeurs Bolt depuis l'API.
    Utilise POST /fleetIntegration/v1/getDrivers selon la documentation Bolt.
    """
    from app.core.config import get_settings
    config = get_settings()
    
    # Utiliser company_id depuis les settings ou celui fourni
    if not company_id:
        # Si pas de company_id spécifique, on essaie de récupérer depuis les settings
        # Pour l'instant, on utilise une valeur par défaut ou on laisse vide
        company_id = config.bolt_default_fleet_id
    
    # Construire le body selon la documentation Bolt
    payload = {
        "company_id": int(company_id) if company_id and company_id.isdigit() else 0,  # Bolt attend un int
        "limit": min(limit, 1000),  # Max 1000 selon la doc
        "offset": offset,
    }
    
    # Appel POST vers l'endpoint Bolt
    data = client.post("/fleetIntegration/v1/getDrivers", payload)
    
    # La réponse Bolt a la structure: { "code": 0, "message": "...", "data": { "drivers": [...] } }
    drivers = data.get("data", {}).get("drivers", [])
    
    for d in drivers:
        # Mapper les champs Bolt vers notre modèle
        driver_uuid = d.get("driver_uuid") or d.get("id")
        db.merge(
            BoltDriver(
                id=driver_uuid,
                org_id=settings.bolt_default_fleet_id or settings.uber_default_org_id or "default_org",
                first_name=d.get("first_name", ""),
                last_name=d.get("last_name", ""),
                email=d.get("email"),
                phone=d.get("phone"),
                active=d.get("state") == "active" if d.get("state") else True,
            )
        )
    db.commit()

