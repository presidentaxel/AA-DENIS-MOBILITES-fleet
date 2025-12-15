from fastapi import APIRouter

from app.api.endpoints import bolt_debug, bolt_drivers, bolt_earnings, bolt_sync, bolt_trips, bolt_vehicles, bolt_state_logs, bolt_driver_earnings

router = APIRouter()

router.include_router(bolt_drivers.router)
router.include_router(bolt_vehicles.router)
router.include_router(bolt_trips.router)  # Contient maintenant /orders
router.include_router(bolt_state_logs.router)
router.include_router(bolt_driver_earnings.router)  # Revenus des drivers
router.include_router(bolt_earnings.router)
router.include_router(bolt_sync.router)
router.include_router(bolt_debug.router)

