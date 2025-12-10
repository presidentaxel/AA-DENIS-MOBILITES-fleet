from fastapi import APIRouter

from app.api.endpoints import fleet_orgs, fleet_drivers, fleet_vehicles, fleet_metrics, fleet_payments, sync

router = APIRouter()

router.include_router(fleet_orgs.router)
router.include_router(fleet_drivers.router)
router.include_router(fleet_vehicles.router)
router.include_router(fleet_metrics.router)
router.include_router(fleet_payments.router)
router.include_router(sync.router)

