from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.constants import DEFAULT_EMBEDDING_DIMENSIONS
from app.domain.entities import User
from app.infrastructure.repositories import (
    ProductEmbeddingRepository,
    SQLAlchemyProductRepository,
)
from app.schemas.product import ProductCreate, ProductRead

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductRead])
async def list_products(
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> list[ProductRead]:
    repo = SQLAlchemyProductRepository(session)
    items = await repo.list_paginated(offset=offset, limit=limit)
    return [
        ProductRead(
            id=p.id,
            name=p.name,
            description=p.description,
            sku=p.sku,
            price=p.price,
            stock_quantity=p.stock_quantity,
            category=p.category,
            created_at=p.created_at,
        )
        for p in items
    ]


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    body: ProductCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> ProductRead:
    repo = SQLAlchemyProductRepository(session)
    p = await repo.create(
        name=body.name,
        description=body.description,
        sku=body.sku,
        price=body.price,
        stock_quantity=body.stock_quantity,
        category=body.category,
    )
    await session.commit()
    return ProductRead(
        id=p.id,
        name=p.name,
        description=p.description,
        sku=p.sku,
        price=p.price,
        stock_quantity=p.stock_quantity,
        category=p.category,
        created_at=p.created_at,
    )


class EmbeddingUpsertBody(BaseModel):
    embedding: list[float] = Field(
        min_length=DEFAULT_EMBEDDING_DIMENSIONS,
        max_length=DEFAULT_EMBEDDING_DIMENSIONS,
    )
    source_text: str | None = None


@router.put("/{product_id}/embedding", status_code=status.HTTP_204_NO_CONTENT)
async def upsert_product_embedding(
    product_id: UUID,
    body: EmbeddingUpsertBody,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> None:
    products = SQLAlchemyProductRepository(session)
    if not await products.get_by_id(product_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product not found")
    emb = ProductEmbeddingRepository(session)
    await emb.upsert_embedding(
        product_id=product_id,
        embedding=body.embedding,
        source_text=body.source_text,
    )
    await session.commit()


class SemanticSearchBody(BaseModel):
    query_embedding: list[float] = Field(
        min_length=DEFAULT_EMBEDDING_DIMENSIONS,
        max_length=DEFAULT_EMBEDDING_DIMENSIONS,
    )
    limit: int = Field(10, ge=1, le=50)


@router.post("/search/semantic")
async def semantic_search(
    body: SemanticSearchBody,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[dict]:
    emb = ProductEmbeddingRepository(session)
    rows = await emb.search_similar(body.query_embedding, limit=body.limit)
    return [{"product_id": str(pid), "name": name, "distance": dist} for pid, name, dist in rows]
