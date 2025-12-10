from pydantic import BaseModel


class Org(BaseModel):
    id: str
    org_id: str
    name: str

    class Config:
        from_attributes = True

