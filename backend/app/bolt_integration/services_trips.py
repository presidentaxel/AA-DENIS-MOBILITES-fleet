import time
from datetime import datetime

from app.core.config import get_settings
from app.core.supabase_db import SupabaseDB
from app.models.bolt_order import BoltOrder
from app.models.bolt_org import BoltOrganization
from app.bolt_integration.bolt_client import BoltClient

settings = get_settings()


def sync_trips(db: SupabaseDB, client: BoltClient, company_id: str | None = None, start: datetime | None = None, end: datetime | None = None, org_id: str | None = None, limit: int = 1000, offset: int = 0, incremental: bool = True) -> None:
    """
    Synchronise les commandes Bolt (orders) depuis l'API getFleetOrders.
    Utilise POST /fleetIntegration/v1/getFleetOrders selon la documentation Bolt.
    
    Args:
        incremental: Si True, récupère le dernier timestamp synchronisé et ne synchronise que les nouvelles commandes.
                    Sinon, synchronise la période spécifiée.
    """
    from app.core import logging as app_logging
    logger = app_logging.get_logger(__name__)
    
    # Déterminer org_id si non fourni
    if not org_id:
        org_id = settings.bolt_default_fleet_id or settings.uber_default_org_id or "default_org"
    
    # Utiliser company_id depuis les paramètres, puis depuis la DB, puis depuis les settings
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
        raise ValueError("company_id est requis pour synchroniser les orders Bolt")
    
    # Mode incrémental : récupérer le dernier timestamp synchronisé
    if incremental and not start:
        # Récupérer le dernier order_created_timestamp pour cette org
        last_order = db.query(BoltOrder).filter(
            BoltOrder.org_id == org_id
        ).order_by(BoltOrder.order_created_timestamp.desc()).first()
        
        if last_order and last_order.order_created_timestamp:
            # Commencer juste après le dernier order synchronisé
            start = datetime.fromtimestamp(last_order.order_created_timestamp + 1)
            logger.info(f"[INCREMENTAL SYNC] Dernier order synchronisé: {start.isoformat()}, reprise à partir de là")
        else:
            # Première sync : 30 jours en arrière
            start = datetime.fromtimestamp(time.time() - (30 * 24 * 60 * 60))
            logger.info(f"[INCREMENTAL SYNC] Première sync, départ depuis 30 jours")
    elif not start:
        # Mode non-incrémental ou start explicitement fourni
        if not start:
            start = datetime.fromtimestamp(time.time() - (30 * 24 * 60 * 60))
    
    # Date de fin : maintenant par défaut
    if not end:
        end = datetime.utcnow()
    
    # Limite : ne jamais aller plus loin que 16 mois en arrière (limite API Bolt)
    max_days_back = 16 * 30  # ~16 mois
    earliest_allowed = datetime.fromtimestamp(time.time() - (max_days_back * 24 * 60 * 60))
    if start < earliest_allowed:
        logger.warning(f"[SYNC] Date de début {start} trop ancienne, limitation à {earliest_allowed}")
        start = earliest_allowed
    
    start_ts = int(start.timestamp())
    end_ts = int(end.timestamp())
    
    # Pagination : récupérer tous les orders
    batch_limit = min(limit, 1000) if limit > 0 else 1000  # Max 1000 selon la doc
    current_offset = offset
    total_saved = 0
    total_skipped = 0
    page = 1
    
    logger.info(f"[SYNC ORDERS] Début synchronisation complète des orders (company_id={company_id}, org_id={org_id}, start_ts={start_ts}, end_ts={end_ts})")
    
    # Récupérer les order_references existants pour cette période une seule fois (pour éviter les doublons)
    existing_orders = db.query(BoltOrder).filter(
        BoltOrder.org_id == org_id,
        BoltOrder.order_created_timestamp >= start_ts,
        BoltOrder.order_created_timestamp <= end_ts
    ).all()
    existing_order_refs = {order.order_reference for order in existing_orders if order.order_reference}
    logger.info(f"[SYNC ORDERS] {len(existing_order_refs)} orders déjà présents pour cette période")
    
    while True:
        # Construire le payload selon la documentation Bolt
        # L'API attend company_ids comme array (même pour un seul ID)
        payload = {
            "company_ids": [int(company_id)],  # Array requis par l'API
            "limit": batch_limit,
            "offset": current_offset,
            "start_ts": start_ts,
            "end_ts": end_ts,
            # time_range_filter_type est optionnel (par défaut: création date)
        }
        
        logger.info(f"[SYNC ORDERS] Page {page}: offset={current_offset}, limit={batch_limit}")
        
        # Appel POST vers l'endpoint Bolt
        data = client.post("/fleetIntegration/v1/getFleetOrders", payload)
        
        # La réponse Bolt a la structure: { "code": 0, "message": "...", "data": { "orders": [...] } }
        if data.get("code") != 0:
            error_msg = data.get("message", "Unknown error")
            raise RuntimeError(f"Bolt API error: {error_msg}")
        
        orders_data = data.get("data", {})
        orders = orders_data.get("orders", [])
        logger.info(f"[SYNC ORDERS] Page {page}: Récupéré {len(orders)} orders depuis Bolt")
        
        if not orders:
            # Plus d'orders à récupérer
            logger.info(f"[SYNC ORDERS] Aucun order supplémentaire, fin de la pagination")
            break
        
        # Sauvegarder les orders de cette page
        saved_count = 0
        skipped_count = 0
        
        try:
            for order in orders:
                order_reference = order.get("order_reference")
                
                # Skip si déjà présent
                if order_reference and order_reference in existing_order_refs:
                    skipped_count += 1
                    continue
                
                # Ajouter à la liste des existants pour éviter les doublons dans les pages suivantes
                if order_reference:
                    existing_order_refs.add(order_reference)
                
                order_price = order.get("order_price", {})
                
                # Extraire les stops (peut être un array)
                order_stops = order.get("order_stops", [])
                
                # Extraire category_info
                category_info = order.get("category_info", {})
                
                bolt_order = BoltOrder(
                    order_reference=order_reference,
                    org_id=org_id,
                    company_id=int(company_id),  # Utiliser le company_id qu'on a passé à l'API
                    company_name=orders_data.get("company_name"),
                    driver_uuid=order.get("driver_uuid"),
                    partner_uuid=order.get("partner_uuid"),
                    driver_name=order.get("driver_name"),
                    driver_phone=order.get("driver_phone"),
                    payment_method=order.get("payment_method"),
                    payment_confirmed_timestamp=order.get("payment_confirmed_timestamp"),
                    order_created_timestamp=order.get("order_created_timestamp"),
                    order_status=order.get("order_status"),
                    driver_cancelled_reason=order.get("driver_cancelled_reason"),
                    vehicle_model=order.get("vehicle_model"),
                    vehicle_license_plate=order.get("vehicle_license_plate"),
                    price_review_reason=order.get("price_review_reason"),
                    pickup_address=order.get("pickup_address"),
                    ride_distance=order.get("ride_distance") or 0,
                    order_accepted_timestamp=order.get("order_accepted_timestamp"),
                    order_pickup_timestamp=order.get("order_pickup_timestamp"),
                    order_drop_off_timestamp=order.get("order_drop_off_timestamp"),
                    order_finished_timestamp=order.get("order_finished_timestamp"),
                    # Prix détaillés (gérer None explicitement)
                    ride_price=order_price.get("ride_price") if order_price.get("ride_price") is not None else 0,
                    booking_fee=order_price.get("booking_fee") if order_price.get("booking_fee") is not None else 0,
                    toll_fee=order_price.get("toll_fee") if order_price.get("toll_fee") is not None else 0,
                    cancellation_fee=order_price.get("cancellation_fee") if order_price.get("cancellation_fee") is not None else 0,
                    tip=order_price.get("tip") if order_price.get("tip") is not None else 0,
                    net_earnings=order_price.get("net_earnings") if order_price.get("net_earnings") is not None else 0,
                    cash_discount=order_price.get("cash_discount") if order_price.get("cash_discount") is not None else 0,
                    in_app_discount=order_price.get("in_app_discount") if order_price.get("in_app_discount") is not None else 0,
                    commission=order_price.get("commission") if order_price.get("commission") is not None else 0,
                    currency=order_price.get("currency") or "EUR",
                    is_scheduled=order.get("is_scheduled", False),
                    category_name=category_info.get("name"),
                    category_seats=category_info.get("seats"),
                    category_vehicle_type=category_info.get("vehicle_type"),
                    order_stops=order_stops if order_stops else None,
                )
                
                db.merge(bolt_order)
                saved_count += 1
            
            # Commit après chaque page pour éviter de perdre les données en cas d'erreur
            db.commit()
            total_saved += saved_count
            total_skipped += skipped_count
            logger.info(f"[SYNC ORDERS] Page {page}: {saved_count} orders sauvegardés, {skipped_count} ignorés (total: {total_saved} sauvegardés, {total_skipped} ignorés)")
            
        except Exception as e:
            db.rollback()
            logger.error(f"[SYNC ORDERS] Erreur lors de la sauvegarde de la page {page}: {e}", exc_info=True)
            raise
        
        # Si on a récupéré moins d'orders que le limit, c'est qu'on a atteint la fin
        if len(orders) < batch_limit:
            logger.info(f"[SYNC ORDERS] Dernière page atteinte ({len(orders)} < {batch_limit})")
            break
        
        # Passer à la page suivante
        current_offset += batch_limit
        page += 1
        
        # Sécurité : éviter les boucles infinies (max 1000 pages = 1M orders max)
        if page > 1000:
            logger.warning(f"[SYNC ORDERS] Limite de sécurité atteinte (1000 pages), arrêt de la synchronisation")
            break
    
    logger.info(f"[SYNC ORDERS] Synchronisation terminée: {total_saved} orders sauvegardés, {total_skipped} déjà présents (ignorés) avec org_id={org_id}")

