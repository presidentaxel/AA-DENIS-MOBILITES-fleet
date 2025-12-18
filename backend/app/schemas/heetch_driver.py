from pydantic import BaseModel


class HeetchDriverBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    image_url: str | None = None
    active: bool = True


class HeetchDriverCreate(HeetchDriverBase):
    org_id: str


class HeetchDriverSchema(HeetchDriverBase):
    id: str
    org_id: str

    class Config:
        from_attributes = True

