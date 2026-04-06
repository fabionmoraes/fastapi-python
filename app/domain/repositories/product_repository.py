from decimal import Decimal
from typing import Protocol
from uuid import UUID

from app.domain.entities import Product


class ProductRepository(Protocol):
    async def list_paginated(self, offset: int, limit: int) -> list[Product]: ...

    async def get_by_id(self, product_id: UUID) -> Product | None: ...

    async def create(
        self,
        *,
        name: str,
        description: str | None,
        sku: str,
        price: Decimal,
        stock_quantity: int,
        category: str | None,
    ) -> Product: ...
