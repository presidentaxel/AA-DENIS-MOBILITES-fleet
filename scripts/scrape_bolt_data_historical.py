#!/usr/bin/env python3
"""
Script pour scraper les données Bolt sur une période historique (6 mois ou 31 jours).
Récupère les données par fenêtres de 7 jours pour tous les chauffeurs.

Usage:
    python scripts/scrape_bolt_data_historical.py [--max-days 180] [--org-id ORG_ID] [--company-id COMPANY_ID]
"""

import argparse
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Ajouter le répertoire backend au path pour les imports
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Charger les variables d'environnement depuis backend/.env
from dotenv import load_dotenv
env_path = backend_dir / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Variables d'environnement chargées depuis: {env_path}")
else:
    print(f"⚠️  Fichier .env non trouvé: {env_path}")

from app.core.config import get_settings
from app.core.db import get_db
from app.bolt_integration.bolt_client import BoltClient
from app.bolt_integration.services_state_logs import sync_state_logs
from app.bolt_integration.services_trips import sync_trips
from app.models.bolt_driver import BoltDriver
from app.models.bolt_org import BoltOrganization
from app.core import logging as app_logging

logger = app_logging.get_logger(__name__)
settings = get_settings()


def get_all_drivers(db, org_id: str) -> list[BoltDriver]:
    """Récupère tous les chauffeurs Bolt pour une organisation."""
    drivers = db.query(BoltDriver).filter(BoltDriver.org_id == org_id).all()
    logger.info(f"Trouvé {len(drivers)} chauffeurs pour org_id={org_id}")
    return drivers


def scrape_data_period(
    db,
    client: BoltClient,
    start_date: datetime,
    end_date: datetime,
    company_id: str,
    org_id: str,
    window_days: int = 7,
) -> dict:
    """
    Scrape les données de tous les chauffeurs sur une période donnée, par fenêtres de 7 jours.
    Les services Bolt récupèrent toutes les données de l'organisation, pas par chauffeur individuel.
    
    Returns:
        dict avec les statistiques de scraping
    """
    stats = {
        "state_logs_windows": 0,
        "orders_windows": 0,
        "errors": [],
    }
    
    current_start = start_date
    window_delta = timedelta(days=window_days)
    
    logger.info(f"Scraping données de {start_date.date()} à {end_date.date()}")
    
    while current_start < end_date:
        # Calculer la fin de la fenêtre (7 jours ou jusqu'à end_date)
        current_end = min(current_start + window_delta, end_date)
        
        try:
            logger.info(f"  Fenêtre: {current_start.date()} -> {current_end.date()}")
            
            # Scraper les state logs pour cette fenêtre (pour tous les chauffeurs)
            try:
                sync_state_logs(
                    db=db,
                    client=client,
                    company_id=company_id,
                    start=current_start,
                    end=current_end,
                    org_id=org_id,
                    incremental=False,  # Mode non-incrémental pour forcer la sync de cette période
                )
                stats["state_logs_windows"] += 1
                logger.info(f"    ✓ State logs synchronisés pour {current_start.date()} -> {current_end.date()}")
            except Exception as e:
                error_msg = f"Erreur state logs {current_start.date()} -> {current_end.date()}: {str(e)}"
                logger.error(f"    ✗ {error_msg}")
                stats["errors"].append(error_msg)
            
            # Scraper les orders pour cette fenêtre (pour tous les chauffeurs)
            try:
                sync_trips(
                    db=db,
                    client=client,
                    company_id=company_id,
                    start=current_start,
                    end=current_end,
                    org_id=org_id,
                    incremental=False,  # Mode non-incrémental
                )
                stats["orders_windows"] += 1
                logger.info(f"    ✓ Orders synchronisés pour {current_start.date()} -> {current_end.date()}")
            except Exception as e:
                error_msg = f"Erreur orders {current_start.date()} -> {current_end.date()}: {str(e)}"
                logger.error(f"    ✗ {error_msg}")
                stats["errors"].append(error_msg)
            
            # Petite pause pour éviter de surcharger l'API
            time.sleep(0.5)
            
        except Exception as e:
            error_msg = f"Erreur générale {current_start.date()} -> {current_end.date()}: {str(e)}"
            logger.error(f"    ✗ {error_msg}")
            stats["errors"].append(error_msg)
        
        # Passer à la fenêtre suivante
        current_start = current_end
    
    return stats


def main():
    parser = argparse.ArgumentParser(description="Scrape les données Bolt historiques")
    parser.add_argument(
        "--max-days",
        type=int,
        default=180,
        help="Nombre maximum de jours à scraper en arrière (défaut: 180 = 6 mois)",
    )
    parser.add_argument(
        "--org-id",
        type=str,
        default=None,
        help="ID de l'organisation (défaut: depuis les settings)",
    )
    parser.add_argument(
        "--company-id",
        type=str,
        default=None,
        help="Company ID Bolt (défaut: depuis la DB ou settings)",
    )
    parser.add_argument(
        "--window-days",
        type=int,
        default=7,
        help="Taille de la fenêtre en jours (défaut: 7)",
    )
    parser.add_argument(
        "--try-31-days",
        action="store_true",
        help="Essayer aussi avec 31 jours si 6 mois échoue (défaut: True)",
    )
    parser.add_argument(
        "--no-try-31-days",
        dest="try_31_days",
        action="store_false",
        help="Ne pas essayer avec 31 jours si 6 mois échoue",
    )
    
    args = parser.parse_args()
    
    # Par défaut, essayer avec 31 jours si --no-try-31-days n'a pas été utilisé
    # Avec action="store_true" et action="store_false", si aucune option n'est spécifiée,
    # try_31_days sera False. On le met à True par défaut sauf si --no-try-31-days est présent.
    if '--no-try-31-days' not in sys.argv:
        args.try_31_days = True
    
    # Initialiser la DB et le client Bolt
    # Utiliser get_db() qui fonctionne avec ou sans Supabase selon la configuration
    try:
        db = next(get_db())
    except RuntimeError as e:
        if "Supabase configuration missing" in str(e):
            logger.error("=" * 80)
            logger.error("ERREUR: Configuration Supabase manquante")
            logger.error("=" * 80)
            logger.error("Le script nécessite les variables d'environnement suivantes:")
            logger.error("  - SUPABASE_URL")
            logger.error("  - SUPABASE_SERVICE_ROLE_KEY")
            logger.error("")
            logger.error("Configurez-les dans backend/.env ou comme variables d'environnement.")
            logger.error("")
            logger.error("Exemple dans backend/.env:")
            logger.error("  SUPABASE_URL=https://xxxxx.supabase.co")
            logger.error("  SUPABASE_SERVICE_ROLE_KEY=your_service_role_key")
            logger.error("=" * 80)
            sys.exit(1)
        else:
            raise
    
    client = BoltClient()
    
    # Déterminer org_id
    org_id = args.org_id or settings.bolt_default_fleet_id or settings.uber_default_org_id
    if not org_id:
        logger.error("org_id est requis. Utilisez --org-id ou configurez BOLT_DEFAULT_FLEET_ID")
        sys.exit(1)
    
    # Déterminer company_id
    company_id = args.company_id
    if not company_id:
        # Essayer de récupérer depuis la DB
        bolt_org = db.query(BoltOrganization).filter(BoltOrganization.org_id == org_id).first()
        if bolt_org:
            company_id = bolt_org.id
            logger.info(f"Utilisation du company_id depuis la DB: {company_id}")
        else:
            # Fallback sur les settings
            company_id = settings.bolt_default_fleet_id
    
    if not company_id:
        logger.error("company_id est requis. Utilisez --company-id ou configurez BOLT_DEFAULT_FLEET_ID")
        sys.exit(1)
    
    # Calculer les dates
    end_date = datetime.utcnow()
    start_date_6months = end_date - timedelta(days=args.max_days)
    start_date_31days = end_date - timedelta(days=31)
    
    logger.info("=" * 80)
    logger.info("SCRAPING DES DONNÉES BOLT HISTORIQUES")
    logger.info("=" * 80)
    logger.info(f"Org ID: {org_id}")
    logger.info(f"Company ID: {company_id}")
    logger.info(f"Période: {start_date_6months.date()} -> {end_date.date()} ({args.max_days} jours)")
    logger.info(f"Fenêtre: {args.window_days} jours")
    logger.info("=" * 80)
    
    # Vérifier qu'il y a des chauffeurs (optionnel, juste pour info)
    drivers = get_all_drivers(db, org_id)
    logger.info(f"Nombre de chauffeurs dans l'organisation: {len(drivers)}")
    
    # Essayer d'abord avec 6 mois (ou max-days)
    logger.info(f"\nTentative avec {args.max_days} jours...")
    try:
        stats = scrape_data_period(
            db=db,
            client=client,
            start_date=start_date_6months,
            end_date=end_date,
            company_id=company_id,
            org_id=org_id,
            window_days=args.window_days,
        )
        
        logger.info("\n" + "=" * 80)
        logger.info("SCRAPING TERMINÉ")
        logger.info("=" * 80)
        logger.info(f"Fenêtres state logs traitées: {stats['state_logs_windows']}")
        logger.info(f"Fenêtres orders traitées: {stats['orders_windows']}")
        logger.info(f"Total erreurs: {len(stats['errors'])}")
        
        if stats["errors"]:
            logger.warning("\nErreurs rencontrées:")
            for error in stats["errors"][:10]:  # Afficher les 10 premières
                logger.warning(f"  - {error}")
            if len(stats["errors"]) > 10:
                logger.warning(f"  ... et {len(stats['errors']) - 10} autres erreurs")
        
    except Exception as e:
        logger.error(f"Erreur lors du scraping: {e}", exc_info=True)
        
        # Si demandé, essayer avec 31 jours
        if args.try_31_days:
            logger.info(f"\nTentative avec 31 jours...")
            try:
                stats = scrape_data_period(
                    db=db,
                    client=client,
                    start_date=start_date_31days,
                    end_date=end_date,
                    company_id=company_id,
                    org_id=org_id,
                    window_days=args.window_days,
                )
                
                logger.info("\n" + "=" * 80)
                logger.info("SCRAPING TERMINÉ (31 jours)")
                logger.info("=" * 80)
                logger.info(f"Fenêtres state logs traitées: {stats['state_logs_windows']}")
                logger.info(f"Fenêtres orders traitées: {stats['orders_windows']}")
                logger.info(f"Total erreurs: {len(stats['errors'])}")
            except Exception as e2:
                logger.error(f"Erreur lors du scraping 31 jours: {e2}", exc_info=True)
                sys.exit(1)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()

