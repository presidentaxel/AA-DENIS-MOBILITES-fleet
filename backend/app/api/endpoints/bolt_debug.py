from fastapi import APIRouter, Depends

import httpx
from app.api.deps import get_current_user
from app.core.db import get_db
from app.core.config import get_settings
from app.models.bolt_driver import BoltDriver
from app.models.bolt_vehicle import BoltVehicle
from app.models.bolt_org import BoltOrganization
from app.bolt_integration.bolt_client import BoltClient

router = APIRouter(prefix="/bolt", tags=["bolt"])

settings = get_settings()


@router.get("/debug/stats")
def get_bolt_stats(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    """Endpoint de debug pour voir les statistiques Bolt dans la base de données."""
    from app.core.supabase_db import SupabaseDB
    
    user_org_id = current_user["org_id"]
    db: SupabaseDB = db  # Type hint pour l'IDE
    
    # Compter les drivers par org_id
    total_drivers = db.query(BoltDriver).count()
    drivers_for_user = db.query(BoltDriver).filter(BoltDriver.org_id == user_org_id).count()
    
    # Compter les véhicules par org_id
    total_vehicles = db.query(BoltVehicle).count()
    vehicles_for_user = db.query(BoltVehicle).filter(BoltVehicle.org_id == user_org_id).count()
    
    # Lister les org_id uniques (via Supabase, on récupère tous et on filtre)
    all_drivers = db.query(BoltDriver).all()
    driver_org_ids = list(set([d.org_id for d in all_drivers]))
    all_vehicles = db.query(BoltVehicle).all()
    vehicle_org_ids = list(set([v.org_id for v in all_vehicles]))
    
    # Compter les organizations Bolt
    total_orgs = db.query(BoltOrganization).count()
    orgs_for_user = db.query(BoltOrganization).filter(BoltOrganization.org_id == user_org_id).all()
    all_orgs = db.query(BoltOrganization).all()
    org_org_ids = list(set([o.org_id for o in all_orgs]))
    
    return {
        "user_org_id": user_org_id,
        "bolt_default_fleet_id": settings.bolt_default_fleet_id,
        "uber_default_org_id": settings.uber_default_org_id,
        "organizations": {
            "total_in_db": total_orgs,
            "for_your_org_id": len(orgs_for_user),
            "company_ids": [org.id for org in orgs_for_user],
            "unique_org_ids": org_org_ids,
        },
        "drivers": {
            "total_in_db": total_drivers,
            "for_your_org_id": drivers_for_user,
            "unique_org_ids": driver_org_ids,
        },
        "vehicles": {
            "total_in_db": total_vehicles,
            "for_your_org_id": vehicles_for_user,
            "unique_org_ids": vehicle_org_ids,
        },
    }


@router.get("/debug/db-info")
def get_db_info(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    """Affiche les informations de connexion à Supabase."""
    from app.core.config import get_settings
    from app.models.bolt_driver import BoltDriver
    
    settings = get_settings()
    
    try:
        # Compter les drivers dans la table via Supabase
        try:
            driver_count = db.query(BoltDriver).count()
        except Exception as e:
            driver_count = f"Erreur: {str(e)}"
        
        return {
            "supabase_url": settings.supabase_url,
            "using_supabase_api": True,
            "driver_count_in_db": driver_count,
            "supabase_configured": bool(settings.supabase_url and settings.supabase_service_role_key),
        }
    except Exception as e:
        return {
            "error": str(e),
            "supabase_url": settings.supabase_url,
            "using_supabase_api": True,
        }


def test_bolt_auth(current_user: dict = Depends(get_current_user)):
    """
    Teste l'authentification Bolt et récupère les company_ids disponibles.
    Utilise les credentials depuis les variables d'environnement.
    """
    if not settings.bolt_client_id or not settings.bolt_client_secret:
        return {
            "status": "error",
            "message": "BOLT_CLIENT_ID et BOLT_CLIENT_SECRET doivent être configurés dans .env",
            "bolt_client_id_set": bool(settings.bolt_client_id),
            "bolt_client_secret_set": bool(settings.bolt_client_secret),
        }
    
    auth_url = str(settings.bolt_auth_url)
    base_url = str(settings.bolt_base_url).rstrip("/")
    
    result = {
        "auth_url": auth_url,
        "base_url": base_url,
        "client_id": settings.bolt_client_id,
        "client_secret_set": bool(settings.bolt_client_secret),
    }
    
    try:
        # Étape 1: Obtenir le token
        print(f"[BOLT TEST] Étape 1: Authentification vers {auth_url}")
        print(f"[BOLT TEST] client_id: {settings.bolt_client_id}")
        
        auth_resp = httpx.post(
            auth_url,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.bolt_client_id,
                "client_secret": settings.bolt_client_secret,
                "scope": "fleet-integration:api",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=20,
        )
        
        auth_resp.raise_for_status()
        auth_data = auth_resp.json()
        
        access_token = auth_data.get("access_token")
        expires_in = auth_data.get("expires_in", 600)
        
        result["auth"] = {
            "status": "success",
            "token_received": bool(access_token),
            "token_preview": access_token[:20] + "..." if access_token else None,
            "expires_in": expires_in,
            "token_type": auth_data.get("token_type"),
            "scope": auth_data.get("scope"),
        }
        
        if not access_token:
            return {
                **result,
                "status": "error",
                "message": "Aucun token reçu de Bolt",
            }
        
        # Étape 2: Appeler getCompanies avec le token
        print(f"[BOLT TEST] Étape 2: Appel getCompanies vers {base_url}/fleetIntegration/v1/getCompanies")
        
        companies_url = f"{base_url}/fleetIntegration/v1/getCompanies"
        companies_resp = httpx.get(
            companies_url,
            headers={
                "accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
            timeout=20,
        )
        
        companies_resp.raise_for_status()
        companies_data = companies_resp.json()
        
        result["companies"] = {
            "status": "success",
            "url": companies_url,
            "response": companies_data,
            "company_ids": companies_data.get("data", {}).get("company_ids", []),
        }
        
        result["status"] = "success"
        result["message"] = f"Authentification réussie. {len(result['companies']['company_ids'])} company_id(s) trouvé(s)"
        
        return result
        
    except httpx.ConnectError as e:
        return {
            **result,
            "status": "error",
            "message": f"Erreur de connexion: {str(e)}",
            "error_type": "ConnectionError",
        }
    except httpx.HTTPStatusError as e:
        error_detail = {
            "status_code": e.response.status_code,
            "response_text": e.response.text[:500],
        }
        try:
            error_detail["response_json"] = e.response.json()
        except:
            pass
        
        return {
            **result,
            "status": "error",
            "message": f"Erreur HTTP {e.response.status_code}",
            "error_type": "HTTPStatusError",
            "error_detail": error_detail,
        }
    except Exception as e:
        return {
            **result,
            "status": "error",
            "message": f"Erreur inattendue: {str(e)}",
            "error_type": type(e).__name__,
        }

