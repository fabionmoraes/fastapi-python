from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(slots=True)
class Product:
    id: UUID
    name: str
    description: str | None
    sku: str
    price: Decimal
    stock_quantity: int
    category: str | None
    created_at: datetime
    updated_at: datetime
