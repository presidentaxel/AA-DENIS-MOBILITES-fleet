import time
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.core.db import get_db
from app.core.supabase_db import SupabaseDB
from app.core import logging as app_logging
from app.heetch_integration.client_manager import get_heetch_client
from app.heetch_integration.services_drivers import sync_drivers_from_earnings
from app.heetch_integration.services_earnings import sync_earnings

logger = app_logging.get_logger(__name__)

router = APIRouter(prefix="/heetch", tags=["heetch"])


@router.post("/sync/drivers")
def sync_heetch_drivers(
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db),
    sms_code: Optional[str] = Query(None, description="Code SMS pour 2FA (si nécessaire)"),
):
    """
    Synchronise les chauffeurs Heetch depuis les données earnings.
    Les drivers sont extraits de la réponse de l'API earnings.
    """
    try:
        from app.models.heetch_driver import HeetchDriver
        
        # Compter AVANT la sync
        count_before = db.query(HeetchDriver).filter(HeetchDriver.org_id == current_user["org_id"]).count()
        
        # Récupérer le client (mis en cache pour conserver l'état)
        client = get_heetch_client(current_user["org_id"])
        
        # Essayer de se connecter automatiquement (avec cookies ou flux complet)
        try:
            client.auto_login(sms_code=sms_code)
            logger.info("[HEETCH] Connexion automatique réussie")
        except ValueError as e:
            # Erreur de configuration (code SMS manquant, etc.)
            return {
                "status": "error",
                "message": str(e),
                "requires_auth": True,
            }
        except Exception as e:
            logger.error(f"[HEETCH] Erreur lors de la connexion automatique: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Erreur de connexion: {str(e)}. Utilisez /heetch/auth/start puis /heetch/auth/complete manuellement.",
                "requires_auth": True,
            }
        
        # Synchroniser les drivers
        sync_drivers_from_earnings(db, client, org_id=current_user["org_id"])
        
        # Compter APRÈS la sync
        count_after = db.query(HeetchDriver).filter(HeetchDriver.org_id == current_user["org_id"]).count()
        
        return {
            "status": "success",
            "message": "Drivers synchronized",
            "count_before": count_before,
            "count_after": count_after,
            "total_drivers_in_db": count_after,
            "org_id_used": current_user["org_id"],
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }


@router.post("/sync/earnings")
def sync_heetch_earnings(
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db),
    start_date: Optional[date] = Query(None, alias="from", description="Date de début (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, alias="to", description="Date de fin (YYYY-MM-DD)"),
    period: str = Query("weekly", description="Période: weekly, monthly"),
    sms_code: Optional[str] = Query(None, description="Code SMS pour 2FA (si nécessaire)"),
):
    """
    Synchronise les earnings Heetch depuis l'API.
    """
    try:
        from app.models.heetch_earning import HeetchEarning
        
        # Compter AVANT la sync
        count_before = db.query(HeetchEarning).filter(HeetchEarning.org_id == current_user["org_id"]).count()
        
        # Récupérer le client (mis en cache pour conserver l'état)
        client = get_heetch_client(current_user["org_id"])
        
        # Essayer de se connecter automatiquement (avec cookies ou flux complet)
        try:
            client.auto_login(sms_code=sms_code)
            logger.info("[HEETCH] Connexion automatique réussie")
        except ValueError as e:
            # Erreur de configuration (code SMS manquant, etc.)
            return {
                "status": "error",
                "message": str(e),
                "requires_auth": True,
            }
        except Exception as e:
            logger.error(f"[HEETCH] Erreur lors de la connexion automatique: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Erreur de connexion: {str(e)}. Utilisez /heetch/auth/start puis /heetch/auth/complete manuellement.",
                "requires_auth": True,
            }
        
        # Synchroniser les earnings
        sync_earnings(
            db,
            client,
            org_id=current_user["org_id"],
            start_date=start_date,
            end_date=end_date,
            period=period
        )
        
        # Compter APRÈS la sync
        count_after = db.query(HeetchEarning).filter(HeetchEarning.org_id == current_user["org_id"]).count()
        
        return {
            "status": "success",
            "message": "Earnings synchronized",
            "count_before": count_before,
            "count_after": count_after,
            "total_earnings_in_db": count_after,
            "org_id_used": current_user["org_id"],
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }

