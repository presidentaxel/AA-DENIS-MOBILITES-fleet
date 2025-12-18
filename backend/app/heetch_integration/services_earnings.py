from datetime import date, timedelta
from typing import Optional

from app.core.config import get_settings
from app.core.supabase_db import SupabaseDB
from app.models.heetch_earning import HeetchEarning
from app.heetch_integration.heetch_client import HeetchClient

settings = get_settings()


def sync_earnings(
    db: SupabaseDB,
    client: HeetchClient,
    org_id: str | None = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    period: str = "weekly"
) -> None:
    """
    Synchronise les earnings Heetch depuis l'API.
    
    Args:
        db: Instance de la base de données
        client: Client Heetch
        org_id: ID de l'organisation
        start_date: Date de début (par défaut: lundi de la semaine en cours)
        end_date: Date de fin (par défaut: aujourd'hui)
        period: Période (weekly, monthly)
    """
    from app.core import logging as app_logging
    
    logger = app_logging.get_logger(__name__)
    
    # Déterminer org_id si non fourni
    if not org_id:
        org_id = settings.uber_default_org_id or "default_org"
    
    # Déterminer les dates si non fournies
    if not end_date:
        end_date = date.today()
    
    if not start_date:
        # Par défaut, commencer au lundi de la semaine en cours
        days_since_monday = end_date.weekday()
        start_date = end_date - timedelta(days=days_since_monday)
    
    logger.info(f"[SYNC HEETCH EARNINGS] Début synchronisation (org_id={org_id}, start={start_date}, end={end_date}, period={period})")
    
    try:
        # Pour weekly, on récupère les earnings semaine par semaine
        # Pour monthly, on récupère mois par mois
        current_date = start_date
        
        total_saved = 0
        
        while current_date <= end_date:
            try:
                # Récupérer les earnings pour cette période
                earnings_data = client.get_earnings(current_date, period=period)
                
                drivers_data = earnings_data.get("drivers", [])
                logger.info(f"[SYNC HEETCH EARNINGS] {len(drivers_data)} drivers pour la période {current_date}")
                
                for driver_data in drivers_data:
                    email = driver_data.get("email")
                    if not email:
                        continue
                    
                    earnings = driver_data.get("earnings", {})
                    
                    # Créer l'ID composite: driver_id_date_period
                    earning_id = f"{email}_{current_date.isoformat()}_{period}"
                    
                    earning = HeetchEarning(
                        id=earning_id,
                        org_id=org_id,
                        driver_id=email,
                        date=current_date,
                        period=period,
                        gross_earnings=earnings.get("gross_earnings", 0),
                        net_earnings=earnings.get("net_earnings", 0),
                        cash_collected=earnings.get("cash_collected", 0),
                        card_gross_earnings=earnings.get("card_gross_earnings", 0),
                        cash_commission_fees=earnings.get("cash_commission_fees", 0),
                        card_commission_fees=earnings.get("card_commission_fees", 0),
                        cancellation_fees=earnings.get("cancellation_fees", 0),
                        cancellation_fee_adjustments=earnings.get("cancellation_fee_adjustments", 0),
                        bonuses=earnings.get("bonuses", 0),
                        terminated_rides=int(earnings.get("terminated_rides", 0)),
                        cancelled_rides=int(earnings.get("cancelled_rides", 0)),
                        cash_discount=earnings.get("cash_discount", 0),
                        currency=earnings_data.get("currency", "EUR"),
                    )
                    
                    db.merge(earning)
                    total_saved += 1
                
                # Passer à la période suivante
                if period == "weekly":
                    current_date += timedelta(days=7)  # Semaine suivante
                elif period == "monthly":
                    # Passer au mois suivant
                    if current_date.month == 12:
                        current_date = date(current_date.year + 1, 1, 1)
                    else:
                        current_date = date(current_date.year, current_date.month + 1, 1)
                else:
                    # Par défaut, semaine suivante
                    current_date += timedelta(days=7)
                
            except Exception as e:
                logger.error(f"[SYNC HEETCH EARNINGS] Erreur pour la période {current_date}: {e}", exc_info=True)
                # Continuer avec la période suivante
                if period == "weekly":
                    current_date += timedelta(days=7)
                else:
                    if current_date.month == 12:
                        current_date = date(current_date.year + 1, 1, 1)
                    else:
                        current_date = date(current_date.year, current_date.month + 1, 1)
                continue
        
        db.commit()
        logger.info(f"[SYNC HEETCH EARNINGS] {total_saved} earnings sauvegardés")
        
    except Exception as e:
        db.rollback()
        logger.error(f"[SYNC HEETCH EARNINGS] Erreur lors de la synchronisation: {e}", exc_info=True)
        raise

