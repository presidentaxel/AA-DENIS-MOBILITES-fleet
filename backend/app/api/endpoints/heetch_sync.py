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
        from app.core.config import get_settings
        settings = get_settings()
        client = get_heetch_client(current_user["org_id"])
        
        # Charger d'abord les cookies depuis la base de données si disponibles
        phone = getattr(settings, 'heetch_login', None)
        if phone:
            # Essayer de charger les cookies depuis la DB d'abord
            cookies_loaded = client._load_cookies_from_db(phone)
            if cookies_loaded:
                logger.info(f"[HEETCH] Cookies chargés depuis la DB pour {phone}")
                # Vérifier si les cookies sont valides (pas expirés selon la date)
                if client._cookies and time.time() < client._cookies_expires_at:
                    logger.info("[HEETCH] Cookies valides trouvés en DB, utilisation sans reconnexion")
                else:
                    logger.warning("[HEETCH] Cookies trouvés en DB mais expirés, reconnexion nécessaire")
                    client._cookies = None
                    client._cookies_expires_at = 0.0
            else:
                logger.info("[HEETCH] Aucun cookie trouvé en DB, connexion initiale nécessaire")
        
        # Vérifier si la session est authentifiée (avec les cookies chargés)
        if not client.ensure_authenticated(phone):
            # Si pas authentifié, faire le login automatique (qui utilisera les cookies sauvegardés si valides)
            try:
                logger.info("[HEETCH] Tentative de connexion automatique...")
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
        else:
            logger.info("[HEETCH] Session déjà authentifiée avec cookies de la DB (pas de reconnexion nécessaire)")
        
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
        from app.core.config import get_settings
        settings = get_settings()
        client = get_heetch_client(current_user["org_id"])
        
        # Vérifier d'abord si la session est déjà authentifiée (cookies valides)
        # Cela évite de refaire le login complet si les cookies sont encore valides
        phone = getattr(settings, 'heetch_login', None)
        if not client.ensure_authenticated(phone):
            # Si pas authentifié, faire le login automatique (qui utilisera les cookies sauvegardés si valides)
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
        else:
            logger.info("[HEETCH] Session déjà authentifiée, utilisation des cookies sauvegardés (pas de reconnexion nécessaire)")
        
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


@router.post("/sync/earnings/last-2-months")
def sync_heetch_earnings_last_2_months(
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db),
    sms_code: Optional[str] = Query(None, description="Code SMS pour 2FA (si nécessaire, uniquement si session expirée)"),
):
    """
    Synchronise les earnings Heetch sur les 2 derniers mois, semaine par semaine.
    Utilise les cookies sauvegardés si disponibles (pas besoin de SMS à chaque fois).
    
    Cette fonction calcule automatiquement le lundi d'il y a 2 mois et synchronise
    chaque semaine jusqu'à aujourd'hui.
    """
    try:
        from app.models.heetch_earning import HeetchEarning
        from app.core.config import get_settings
        settings = get_settings()
        
        # Compter AVANT la sync
        count_before = db.query(HeetchEarning).filter(HeetchEarning.org_id == current_user["org_id"]).count()
        
        # Récupérer le client (mis en cache pour conserver l'état)
        client = get_heetch_client(current_user["org_id"])
        
        # Charger d'abord les cookies depuis la base de données si disponibles
        phone = getattr(settings, 'heetch_login', None)
        if phone:
            # Essayer de charger les cookies depuis la DB d'abord
            cookies_loaded = client._load_cookies_from_db(phone)
            if cookies_loaded:
                logger.info(f"[HEETCH] Cookies chargés depuis la DB pour {phone}")
                # Vérifier si les cookies sont valides (pas expirés selon la date)
                if client._cookies and time.time() < client._cookies_expires_at:
                    logger.info("[HEETCH] Cookies valides trouvés en DB, utilisation sans reconnexion")
                else:
                    logger.warning("[HEETCH] Cookies trouvés en DB mais expirés, reconnexion nécessaire")
                    client._cookies = None
                    client._cookies_expires_at = 0.0
            else:
                logger.info("[HEETCH] Aucun cookie trouvé en DB, connexion initiale nécessaire")
        
        # Vérifier si la session est authentifiée (avec les cookies chargés)
        if not client.ensure_authenticated(phone):
            # Si pas authentifié, faire le login automatique (qui utilisera les cookies sauvegardés si valides)
            try:
                logger.info("[HEETCH] Tentative de connexion automatique...")
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
        else:
            logger.info("[HEETCH] Session déjà authentifiée avec cookies de la DB (pas de reconnexion nécessaire)")
        
        # Calculer la plage de dates : 2 mois en arrière jusqu'à aujourd'hui
        today = date.today()
        # Trouver le lundi de cette semaine
        days_since_monday = today.weekday()
        end_date = today - timedelta(days=days_since_monday)  # Dernier lundi
        
        # Calculer il y a 2 mois (environ 60 jours)
        # On prend le lundi de la semaine il y a ~8 semaines (56 jours)
        start_date = end_date - timedelta(days=56)  # 8 semaines = 2 mois environ
        # S'assurer que c'est un lundi
        if start_date.weekday() != 0:
            # Si ce n'est pas un lundi, remonter au lundi précédent
            start_date = start_date - timedelta(days=start_date.weekday())
        
        logger.info(f"[HEETCH SYNC LAST 2 MONTHS] Synchronisation de {start_date} à {end_date} (environ 8 semaines)")
        
        # Synchroniser semaine par semaine
        sync_earnings(
            db,
            client,
            org_id=current_user["org_id"],
            start_date=start_date,
            end_date=end_date,
            period="weekly"
        )
        
        # Compter APRÈS la sync
        count_after = db.query(HeetchEarning).filter(HeetchEarning.org_id == current_user["org_id"]).count()
        
        return {
            "status": "success",
            "message": f"Earnings synchronized for last 2 months (from {start_date} to {end_date})",
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "weeks_synced": ((end_date - start_date).days // 7) + 1,
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

