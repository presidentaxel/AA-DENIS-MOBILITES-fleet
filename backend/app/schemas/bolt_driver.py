from pydantic import BaseModel, EmailStr


class BoltDriverSchema(BaseModel):
    id: str
    org_id: str
    first_name: str
    last_name: str
    email: EmailStr | None = None
    phone: str | None = None
    active: bool = True

    class Config:
        from_attributes = True

