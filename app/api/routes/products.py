from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.constants import DEFAULT_EMBEDDING_DIMENSIONS
from app.domain.entities import User
from app.infrastructure.embeddings import EmbeddingProviderError, embed_text
from app.infrastructure.embeddings.product_text import build_index_text
from app.infrastructure.repositories import (
    ProductEmbeddingRepository,
    ProductMetricRepository,
    SQLAlchemyProductRepository,
)
from app.schemas.product import (
    ProductCreate,
    ProductEmbeddingRead,
    ProductMetricRead,
    ProductRead,
)

router = APIRouter(prefix="/products", tags=["products"])


async def _generate_and_persist_embedding(
    session: AsyncSession,
    product_id: UUID,
) -> ProductEmbeddingRead:
    products = SQLAlchemyProductRepository(session)
    p = await products.get_by_id(product_id)
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product not found")

    source = build_index_text(
        name=p.name,
        description=p.description,
        sku=p.sku,
        category=p.category,
    )
    try:
        vector = await embed_text(source)
    except EmbeddingProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e

    emb = ProductEmbeddingRepository(session)
    await emb.upsert_embedding(
        product_id=product_id,
        embedding=vector,
        source_text=source,
    )
    await session.commit()

    row = await emb.get_by_product_id(product_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="embedding not persisted",
        )
    return ProductEmbeddingRead(
        id=row.id,
        product_id=row.product_id,
        embedding=list(row.embedding),
        source_text=row.source_text,
        created_at=row.created_at,
    )


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


@router.put(
    "/{product_id}/embedding",
    response_model=ProductEmbeddingRead,
    summary="Gerar e gravar embedding",
    description=(
        "Monta texto a partir do produto (nome, descrição, SKU, categoria), gera o vetor com o "
        "provedor configurado (`EMBEDDING_PROVIDER`: **dummy**, **local** ou **openai**) e faz "
        "upsert em `product_embeddings`. Não envie vetor no JSON; o corpo é opcional/vazio."
    ),
)
async def upsert_product_embedding(
    product_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> ProductEmbeddingRead:
    return await _generate_and_persist_embedding(session, product_id)


class ProductMetricBody(BaseModel):
    """Incrementa `views` e `revenue` no bucket; se já existir linha, soma (upsert)."""

    bucket: datetime = Field(
        description="Início do intervalo agregado (ex.: meia-noite UTC do dia).",
    )
    views: int = Field(0, ge=0)
    revenue: Decimal = Field(default_factory=lambda: Decimal("0"), ge=0)


@router.get(
    "/{product_id}/metrics",
    response_model=list[ProductMetricRead],
    summary="Listar métricas por intervalo de buckets",
)
async def list_product_metrics(
    product_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    from_bucket: datetime = Query(
        ...,
        alias="from",
        description="Início do intervalo de consulta (inclusivo).",
    ),
    to_bucket: datetime = Query(
        ...,
        alias="to",
        description="Fim do intervalo de consulta (inclusivo).",
    ),
) -> list[ProductMetricRead]:
    products = SQLAlchemyProductRepository(session)
    if not await products.get_by_id(product_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product not found")
    repo = ProductMetricRepository(session)
    rows = await repo.list_for_product(
        product_id, from_bucket=from_bucket, to_bucket=to_bucket
    )
    return [
        ProductMetricRead(
            bucket=r.bucket,
            product_id=r.product_id,
            views=r.views,
            revenue=r.revenue,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.post(
    "/{product_id}/metrics",
    response_model=ProductMetricRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar métricas em um bucket (somatório)",
    description=(
        "Grava em `product_metrics` (Timescale). Mesmo `(bucket, product_id)` de novo: soma "
        "`views` e `revenue` à linha existente."
    ),
)
async def append_product_metrics(
    product_id: UUID,
    body: ProductMetricBody,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> ProductMetricRead:
    products = SQLAlchemyProductRepository(session)
    if not await products.get_by_id(product_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product not found")
    repo = ProductMetricRepository(session)
    await repo.upsert_add(
        product_id=product_id,
        bucket=body.bucket,
        views_delta=body.views,
        revenue_delta=body.revenue,
    )
    await session.commit()
    row = await repo.get_bucket(product_id, body.bucket)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="metric row not found after upsert",
        )
    return ProductMetricRead(
        bucket=row.bucket,
        product_id=row.product_id,
        views=row.views,
        revenue=row.revenue,
        created_at=row.created_at,
    )


class SemanticSearchBody(BaseModel):
    query_embedding: list[float] = Field(
        min_length=DEFAULT_EMBEDDING_DIMENSIONS,
        max_length=DEFAULT_EMBEDDING_DIMENSIONS,
    )
    limit: int = Field(10, ge=1, le=50)


class SemanticSearchByTextBody(BaseModel):
    """Busca por texto; o vetor é gerado com o mesmo modelo da indexação (OpenAI)."""

    query: str = Field(
        min_length=1,
        max_length=4096,
        description="Texto da busca em linguagem natural",
    )
    limit: int = Field(10, ge=1, le=50)


def _semantic_hits(rows: list[tuple[UUID, str, float]]) -> list[dict[str, str | float]]:
    return [{"product_id": str(pid), "name": name, "distance": dist} for pid, name, dist in rows]


@router.post(
    "/search/semantic/text",
    summary="Busca semântica por texto",
    description=(
        "Converte `query` em embedding com o mesmo provedor de `PUT .../products/{id}/embedding` "
        "(local ou OpenAI) e busca por similaridade no PGVector."
    ),
)
async def semantic_search_by_text(
    body: SemanticSearchByTextBody,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[dict]:
    try:
        vector = await embed_text(body.query.strip())
    except EmbeddingProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    emb = ProductEmbeddingRepository(session)
    rows = await emb.search_similar(vector, limit=body.limit)
    return _semantic_hits(rows)


@router.post("/search/semantic")
async def semantic_search(
    body: SemanticSearchBody,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[dict]:
    emb = ProductEmbeddingRepository(session)
    rows = await emb.search_similar(body.query_embedding, limit=body.limit)
    return _semantic_hits(rows)
