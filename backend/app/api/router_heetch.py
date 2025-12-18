from fastapi import APIRouter

from app.api.endpoints import heetch_auth, heetch_drivers, heetch_earnings, heetch_sync

router = APIRouter()

router.include_router(heetch_auth.router)
router.include_router(heetch_drivers.router)
router.include_router(heetch_earnings.router)
router.include_router(heetch_sync.router)

