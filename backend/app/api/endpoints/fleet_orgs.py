from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.org import UberOrganization
from app.schemas.org import Org

router = APIRouter()


@router.get("/orgs", response_model=list[Org])
def list_orgs(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    orgs = db.query(UberOrganization).filter(UberOrganization.org_id == current_user["org_id"]).all()
    return orgs

