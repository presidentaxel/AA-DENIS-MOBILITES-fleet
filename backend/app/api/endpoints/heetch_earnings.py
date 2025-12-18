from datetime import date

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.core.db import get_db
from app.core.supabase_db import SupabaseDB
from app.models.heetch_earning import HeetchEarning
from app.schemas.heetch_earning import HeetchEarningSchema

router = APIRouter(prefix="/heetch", tags=["heetch"])


@router.get("/drivers/{driver_id}/earnings", response_model=list[HeetchEarningSchema])
def list_heetch_earnings(
    driver_id: str,
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db),
    start: date = Query(..., alias="from"),
    end: date = Query(..., alias="to"),
    period: str = Query("weekly", description="Période: weekly, monthly"),
):
    return (
        db.query(HeetchEarning)
        .filter(HeetchEarning.org_id == current_user["org_id"])
        .filter(HeetchEarning.driver_id == driver_id)
        .filter(HeetchEarning.date >= start)
        .filter(HeetchEarning.date <= end)
        .filter(HeetchEarning.period == period)
        .order_by(HeetchEarning.date.desc())
        .all()
    )


@router.get("/earnings", response_model=list[HeetchEarningSchema])
def list_all_heetch_earnings(
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db),
    start: date = Query(..., alias="from"),
    end: date = Query(..., alias="to"),
    period: str = Query("weekly", description="Période: weekly, monthly"),
):
    return (
        db.query(HeetchEarning)
        .filter(HeetchEarning.org_id == current_user["org_id"])
        .filter(HeetchEarning.date >= start)
        .filter(HeetchEarning.date <= end)
        .filter(HeetchEarning.period == period)
        .order_by(HeetchEarning.date.desc())
        .all()
    )

