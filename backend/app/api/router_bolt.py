from fastapi import APIRouter

from app.api.endpoints import bolt_drivers, bolt_vehicles, bolt_trips, bolt_earnings

router = APIRouter()

router.include_router(bolt_drivers.router)
router.include_router(bolt_vehicles.router)
router.include_router(bolt_trips.router)
router.include_router(bolt_earnings.router)

