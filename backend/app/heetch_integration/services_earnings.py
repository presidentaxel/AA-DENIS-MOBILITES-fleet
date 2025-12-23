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
                
                # Extraire start_date et end_date depuis summary
                period_start_date = current_date
                period_end_date = current_date
                summary = earnings_data.get("summary", {})
                if period in summary:
                    period_info = summary[period]
                    if "start_date" in period_info:
                        from datetime import datetime
                        start_date_str = period_info["start_date"]
                        # Parser la date ISO avec timezone (format: "2025-12-22T00:00:00+01:00")
                        if isinstance(start_date_str, str):
                            try:
                                # Enlever le timezone pour parser juste la date
                                start_date_str_clean = start_date_str.split("T")[0]
                                period_start_date = datetime.fromisoformat(start_date_str_clean).date()
                            except (ValueError, AttributeError) as e:
                                logger.warning(f"[SYNC HEETCH EARNINGS] Impossible de parser start_date: {start_date_str}, erreur: {e}")
                                period_start_date = current_date
                    if "end_date" in period_info:
                        from datetime import datetime
                        end_date_str = period_info["end_date"]
                        if isinstance(end_date_str, str):
                            try:
                                # Enlever le timezone pour parser juste la date
                                end_date_str_clean = end_date_str.split("T")[0]
                                period_end_date = datetime.fromisoformat(end_date_str_clean).date()
                            except (ValueError, AttributeError) as e:
                                logger.warning(f"[SYNC HEETCH EARNINGS] Impossible de parser end_date: {end_date_str}, erreur: {e}")
                                period_end_date = current_date
                
                drivers_data = earnings_data.get("drivers", [])
                logger.info(f"[SYNC HEETCH EARNINGS] {len(drivers_data)} drivers pour la période {period_start_date} - {period_end_date}")
                
                for driver_data in drivers_data:
                    email = driver_data.get("email")
                    if not email:
                        continue
                    
                    earnings = driver_data.get("earnings", {})
                    
                    # Créer l'ID composite: driver_id_date_period
                    earning_id = f"{email}_{period_start_date.isoformat()}_{period}"
                    
                    # Fonction helper pour convertir None en 0 ou None selon le champ
                    def get_float_or_none(value, default=0):
                        if value is None:
                            return None
                        try:
                            return float(value)
                        except (TypeError, ValueError):
                            return default
                    
                    earning = HeetchEarning(
                        id=earning_id,
                        org_id=org_id,
                        driver_id=email,
                        date=period_start_date,  # Utiliser la date de début réelle
                        period=period,
                        start_date=period_start_date,
                        end_date=period_end_date,
                        gross_earnings=earnings.get("gross_earnings", 0) or 0,
                        net_earnings=earnings.get("net_earnings", 0) or 0,
                        cash_collected=earnings.get("cash_collected", 0) or 0,
                        card_gross_earnings=earnings.get("card_gross_earnings", 0) or 0,
                        cash_commission_fees=earnings.get("cash_commission_fees", 0) or 0,
                        card_commission_fees=earnings.get("card_commission_fees", 0) or 0,
                        cancellation_fees=earnings.get("cancellation_fees", 0) or 0,
                        cancellation_fee_adjustments=earnings.get("cancellation_fee_adjustments", 0) or 0,
                        bonuses=earnings.get("bonuses", 0) or 0,
                        terminated_rides=int(earnings.get("terminated_rides", 0) or 0),
                        cancelled_rides=int(earnings.get("cancelled_rides", 0) or 0),
                        cash_discount=earnings.get("cash_discount", 0) or 0,
                        unpaid_cash_rides_refunds=get_float_or_none(earnings.get("unpaid_cash_rides_refunds")),
                        debt=get_float_or_none(earnings.get("debt")),
                        money_transfer_amount=get_float_or_none(earnings.get("money_transfer_amount")),
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

