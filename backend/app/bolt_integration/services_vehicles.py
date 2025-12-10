from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.bolt_vehicle import BoltVehicle
from app.bolt_integration.bolt_client import BoltClient

settings = get_settings()


def sync_vehicles(db: Session, client: BoltClient, company_id: str | None = None, limit: int = 100, offset: int = 0) -> None:
    """
    Synchronise les véhicules Bolt depuis l'API.
    Utilise POST /fleetIntegration/v1/getVehicles selon la documentation Bolt.
    """
    from app.core.config import get_settings
    config = get_settings()
    
    # Utiliser company_id depuis les settings ou celui fourni
    if not company_id:
        company_id = config.bolt_default_fleet_id
    
    # Construire le body selon la documentation Bolt
    payload = {
        "company_id": int(company_id) if company_id and company_id.isdigit() else 0,  # Bolt attend un int
        "limit": min(limit, 100),  # Max 100 selon la doc
        "offset": offset,
    }
    
    # Appel POST vers l'endpoint Bolt
    data = client.post("/fleetIntegration/v1/getVehicles", payload)
    
    # La réponse Bolt a la structure: { "code": 0, "message": "...", "data": { "vehicles": [...] } }
    vehicles = data.get("data", {}).get("vehicles", [])
    
    for v in vehicles:
        vehicle_uuid = v.get("uuid") or v.get("id")
        db.merge(
            BoltVehicle(
                id=vehicle_uuid,
                org_id=settings.bolt_default_fleet_id or settings.uber_default_org_id or "default_org",
                plate=v.get("reg_number", ""),  # Bolt utilise "reg_number"
                model=v.get("model"),
                provider_vehicle_id=vehicle_uuid,
            )
        )
    db.commit()

