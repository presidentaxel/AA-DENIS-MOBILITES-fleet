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
    start: date = Query(..., alias="from", description="Date de début (YYYY-MM-DD) - date de début de période, ex: 2025-12-22 (lundi)"),
    end: date = Query(..., alias="to", description="Date de fin (YYYY-MM-DD) - date de fin de période, ex: 2025-12-28 (dimanche)"),
    period: str = Query("weekly", description="Période: weekly, monthly"),
):
    """
    Liste les earnings Heetch depuis la base de données.
    
    Note: Les données doivent être synchronisées via /heetch/sync/earnings avant d'être disponibles.
    
    Pour weekly: 
    - 'from' doit être le lundi de la semaine (ex: 2025-12-22)
    - 'to' doit être le dimanche de la semaine (ex: 2025-12-28)
    
    L'API Heetch utilise un seul paramètre 'date' (le lundi), mais cet endpoint filtre par plage de dates
    pour permettre la récupération de plusieurs périodes en une seule requête.
    """
    return (
        db.query(HeetchEarning)
        .filter(HeetchEarning.org_id == current_user["org_id"])
        .filter(HeetchEarning.date >= start)  # date est la date de début de période (lundi)
        .filter(HeetchEarning.date <= end)    # Filtrer jusqu'à la date de fin
        .filter(HeetchEarning.period == period)
        .order_by(HeetchEarning.date.desc())
        .all()
    )

