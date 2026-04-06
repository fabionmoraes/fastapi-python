from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class ClientRead(BaseModel):
    id: UUID
    legal_name: str
    trade_name: str | None
    email: EmailStr
    phone: str | None
    document: str
    segment: str | None
    city: str | None
    country: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ClientCreate(BaseModel):
    legal_name: str = Field(min_length=1, max_length=255)
    trade_name: str | None = None
    email: EmailStr
    phone: str | None = None
    document: str = Field(min_length=5, max_length=32)
    segment: str | None = None
    city: str | None = None
    country: str = Field(default="BR", min_length=2, max_length=2)
