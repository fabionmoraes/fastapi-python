"""Dados de exemplo (executar com DATABASE_URL no ambiente)."""

import asyncio
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.infrastructure.database.models import ClientModel, ProductModel
from app.infrastructure.database.session import AsyncSessionLocal
from app.infrastructure.repositories import (
    SQLAlchemyClientRepository,
    SQLAlchemyProductRepository,
    SQLAlchemyUserRepository,
)


async def main() -> None:
    async with AsyncSessionLocal() as session:
        await _seed(session)
        await session.commit()
        print("seed ok")


async def _seed(session: AsyncSession) -> None:
    users = SQLAlchemyUserRepository(session)
    if not await users.get_by_email("ok1@example.com"):
        await users.create(
            email="ok1@example.com",
            full_name="Admin Demo",
            hashed_password=hash_password("admin12345"),
        )

    products = SQLAlchemyProductRepository(session)
    existing_sku = await session.execute(
        select(ProductModel.sku).where(ProductModel.sku == "SKU-DEMO-001")
    )
    if existing_sku.scalar_one_or_none() is None:
        await products.create(
            name="Notebook Pro 14",
            description="Ultrabook para produtividade e desenvolvimento.",
            sku="SKU-DEMO-001",
            price=Decimal("8999.90"),
            stock_quantity=42,
            category="eletrônicos",
        )

    clients = SQLAlchemyClientRepository(session)
    existing_doc = await session.execute(
        select(ClientModel.id).where(ClientModel.document == "12.345.678/0001-90")
    )
    if existing_doc.scalar_one_or_none() is None:
        await clients.create(
            legal_name="Demo Tech Soluções Ltda",
            trade_name="Demo Tech",
            email="contato@demotech.local",
            phone="+55 11 99999-0000",
            document="12.345.678/0001-90",
            segment="tecnologia",
            city="São Paulo",
            country="BR",
        )


if __name__ == "__main__":
    asyncio.run(main())
