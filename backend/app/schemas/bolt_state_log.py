from typing import Optional, Dict, Any
from pydantic import BaseModel


class BoltStateLogSchema(BaseModel):
    id: str
    org_id: str
    driver_uuid: str
    vehicle_uuid: Optional[str] = None
    created: int
    state: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    active_categories: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

