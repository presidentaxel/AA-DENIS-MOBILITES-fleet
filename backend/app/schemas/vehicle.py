from pydantic import BaseModel


class Vehicle(BaseModel):
    uuid: str
    org_id: str
    plate: str
    model: str | None = None

    class Config:
        from_attributes = True

