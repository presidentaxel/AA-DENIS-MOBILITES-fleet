from pydantic import BaseModel


class BoltVehicleSchema(BaseModel):
    id: str
    org_id: str
    provider_vehicle_id: str | None = None
    plate: str
    model: str | None = None

    class Config:
        from_attributes = True

