from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Product
from app.infrastructure.database.models import ProductModel


def _to_domain(row: ProductModel) -> Product:
    return Product(
        id=row.id,
        name=row.name,
        description=row.description,
        sku=row.sku,
        price=row.price,
        stock_quantity=row.stock_quantity,
        category=row.category,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SQLAlchemyProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_paginated(self, offset: int, limit: int) -> list[Product]:
        stmt = (
            select(ProductModel).order_by(ProductModel.created_at.desc()).offset(offset).limit(limit)
        )
        result = await self._session.execute(stmt)
        return [_to_domain(r) for r in result.scalars().all()]

    async def get_by_id(self, product_id: UUID) -> Product | None:
        row = await self._session.get(ProductModel, product_id)
        return _to_domain(row) if row else None

    async def create(
        self,
        *,
        name: str,
        description: str | None,
        sku: str,
        price: Decimal,
        stock_quantity: int,
        category: str | None,
    ) -> Product:
        model = ProductModel(
            name=name,
            description=description,
            sku=sku,
            price=price,
            stock_quantity=stock_quantity,
            category=category,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_domain(model)
