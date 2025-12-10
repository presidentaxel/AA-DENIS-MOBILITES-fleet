from pydantic import BaseModel, EmailStr


class Driver(BaseModel):
    uuid: str
    org_id: str
    name: str
    email: EmailStr | None = None

    class Config:
        from_attributes = True

