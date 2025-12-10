from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.router_fleet import router as fleet_router
from app.api.router_bolt import router as bolt_router
from app.auth.routes_auth import router as auth_router
from app.core import logging as app_logging
from app.core.db import engine
from app.models import Base
from app.webhooks.routes_webhooks import router as webhook_router


def create_app() -> FastAPI:
    app_logging.setup_logging()
    app = FastAPI(title="AA Denis Mobilités – Fleet Manager API")

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
        # For dev/local: ensure tables exist. In Supabase, prefer managed migrations with RLS.
        Base.metadata.create_all(bind=engine)

    return app


app = create_app()


@app.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}

