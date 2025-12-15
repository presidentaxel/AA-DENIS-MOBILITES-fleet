from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.router_fleet import router as fleet_router
from app.api.router_bolt import router as bolt_router
from app.auth.routes_auth import router as auth_router
from app.core import logging as app_logging
# Désactiver la création automatique des tables car on utilise Supabase
# from app.core.db import engine
# from app.models import Base
from app.webhooks.routes_webhooks import router as webhook_router


def create_app() -> FastAPI:
    app_logging.setup_logging()
    
    app = FastAPI(
        title="AA Denis Mobilités – Fleet Manager API",
        description="""
        API REST sécurisée pour gérer les flottes Uber et Bolt.
        
        ## Authentification
        
        Pour utiliser cette API :
        
        1. Connectez-vous via `/auth/login` pour obtenir un `access_token`
        2. Cliquez sur le bouton **"Authorize"** en haut à droite de cette page
        3. Dans le champ "Value", entrez votre `access_token` (obtenu à l'étape 1)
        4. Cliquez sur **"Authorize"** puis **"Close"**
        5. Tous les endpoints protégés utiliseront automatiquement ce token
        
        **Note** : Le token est valide pendant 60 minutes. Après expiration, reconnectez-vous pour obtenir un nouveau token.
        
        ## Endpoints
        
        - **Auth** : Authentification et gestion des utilisateurs
        - **Fleet** : Endpoints pour les données Uber
        - **Bolt** : Endpoints pour les données Bolt
        - **Webhooks** : Webhooks pour les notifications
        
        ## Documentation complète
        
        Pour un guide complet du fonctionnement et de l'utilisation de l'API, consultez `docs/API_GUIDE.md`.
        """,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Instrument Prometheus before app starts (must be before routers)
    Instrumentator().instrument(app).expose(app, include_in_schema=False)

    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(fleet_router, prefix="/fleet", tags=["fleet"])
    app.include_router(bolt_router, tags=["bolt"])
    app.include_router(webhook_router, prefix="/webhooks", tags=["webhooks"])

    @app.on_event("startup")
    def on_startup() -> None:
        # Tables gérées via Supabase, pas besoin de créer automatiquement
        # Les tables doivent être créées via le schéma SQL dans Supabase
        
        # Synchronisation automatique au démarrage
        from app.core.config import get_settings
        from app.core.supabase_db import SupabaseDB
        from app.core.supabase_client import get_supabase_client
        from app.bolt_integration.services_sync_all import sync_all_bolt_data
        from app.core import logging as app_logging
        import threading
        
        logger = app_logging.get_logger(__name__)
        settings = get_settings()
        
        def sync_on_startup():
            try:
                # Utiliser org_id par défaut
                org_id = settings.uber_default_org_id or "default_org"
                logger.info(f"[STARTUP SYNC] Déclenchement sync automatique au démarrage pour org_id={org_id}")
                
                supabase_client = get_supabase_client()
                db = SupabaseDB(supabase_client)
                
                # Synchroniser uniquement les données légères au démarrage (orgs, drivers, vehicles)
                # Les données lourdes (orders, state_logs) sont synchronisées via le scheduler quotidien
                from app.bolt_integration.services_orgs import sync_orgs
                from app.bolt_integration.services_drivers import sync_drivers
                from app.bolt_integration.services_vehicles import sync_vehicles
                from app.bolt_integration.bolt_client import BoltClient
                from app.models.bolt_driver import BoltDriver
                from app.models.bolt_vehicle import BoltVehicle
                
                client = BoltClient()
                
                # Sync organizations
                sync_orgs(db, client, org_id=org_id)
                
                # Sync drivers
                sync_drivers(db, client, org_id=org_id)
                driver_count = db.query(BoltDriver).filter(BoltDriver.org_id == org_id).count()
                
                # Sync vehicles
                sync_vehicles(db, client, org_id=org_id)
                vehicle_count = db.query(BoltVehicle).filter(BoltVehicle.org_id == org_id).count()
                
                logger.info(f"[STARTUP SYNC] Résultats: drivers={driver_count}, vehicles={vehicle_count}")
                logger.info(f"[STARTUP SYNC] Sync légère terminée. Orders et state_logs seront synchronisés par le scheduler quotidien.")
            except Exception as e:
                logger.error(f"[STARTUP SYNC] Erreur lors de la sync automatique au démarrage: {str(e)}", exc_info=True)
        
        # Lancer la sync en arrière-plan pour ne pas bloquer le démarrage
        sync_thread = threading.Thread(target=sync_on_startup, daemon=True)
        sync_thread.start()
        logger.info("[STARTUP] Synchronisation automatique Bolt démarrée en arrière-plan (données légères uniquement)")
        
        # Démarrer le scheduler pour les tâches périodiques
        try:
            from app.jobs.scheduler import create_scheduler
            scheduler = create_scheduler()
            scheduler.start()
            logger.info("[STARTUP] Scheduler démarré (sync quotidienne des données lourdes à 2h)")
        except Exception as e:
            logger.error(f"[STARTUP] Erreur lors du démarrage du scheduler: {str(e)}", exc_info=True)

    return app


app = create_app()


@app.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}

