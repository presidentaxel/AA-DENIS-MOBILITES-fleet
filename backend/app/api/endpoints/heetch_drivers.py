from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.core.db import get_db
from app.core.supabase_db import SupabaseDB
from app.models.heetch_driver import HeetchDriver
from app.schemas.heetch_driver import HeetchDriverSchema

router = APIRouter(prefix="/heetch", tags=["heetch"])


@router.get("/drivers", response_model=list[HeetchDriverSchema])
def list_heetch_drivers(
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db),
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    return (
        db.query(HeetchDriver)
        .filter(HeetchDriver.org_id == current_user["org_id"])
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/drivers/{driver_id}", response_model=HeetchDriverSchema | None)
def get_heetch_driver(driver_id: str, current_user: dict = Depends(get_current_user), db: SupabaseDB = Depends(get_db)):
    return (
        db.query(HeetchDriver)
        .filter(HeetchDriver.org_id == current_user["org_id"])
        .filter(HeetchDriver.id == driver_id)
        .first()
    )

