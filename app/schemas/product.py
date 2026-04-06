from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProductRead(BaseModel):
    id: UUID
    name: str
    description: str | None
    sku: str
    price: Decimal
    stock_quantity: int
    category: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    sku: str = Field(min_length=1, max_length=64)
    price: Decimal = Field(ge=0)
    stock_quantity: int = Field(ge=0)
    category: str | None = None
