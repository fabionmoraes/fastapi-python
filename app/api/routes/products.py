from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.constants import DEFAULT_EMBEDDING_DIMENSIONS
from app.domain.entities import User
from app.infrastructure.embeddings import EmbeddingProviderError, embed_text_openai
from app.infrastructure.embeddings.product_text import build_index_text
from app.infrastructure.repositories import (
    ProductEmbeddingRepository,
    SQLAlchemyProductRepository,
)
from app.schemas.product import ProductCreate, ProductEmbeddingRead, ProductRead

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


@router.post(
    "/{product_id}/embedding/generate",
    response_model=ProductEmbeddingRead,
    summary="Gerar embedding a partir do produto (OpenAI)",
    description=(
        "Monta um texto com nome, descrição, SKU e categoria, chama a API de embeddings da "
        "**OpenAI** (não é o OpenAPI/Swagger) e grava o vetor em `product_embeddings`. "
        "Requer `OPENAI_API_KEY` no ambiente."
    ),
)
async def generate_product_embedding(
    product_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
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
        vector = await embed_text_openai(source)
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


class EmbeddingUpsertBody(BaseModel):
    embedding: list[float] = Field(
        min_length=DEFAULT_EMBEDDING_DIMENSIONS,
        max_length=DEFAULT_EMBEDDING_DIMENSIONS,
    )
    source_text: str | None = None


@router.get("/{product_id}/embedding", response_model=ProductEmbeddingRead)
async def get_product_embedding(
    product_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> ProductEmbeddingRead:
    """Retorna o vetor salvo em `product_embeddings` (exemplo de resposta no OpenAPI /docs)."""
    products = SQLAlchemyProductRepository(session)
    if not await products.get_by_id(product_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product not found")
    emb = ProductEmbeddingRepository(session)
    row = await emb.get_by_product_id(product_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="embedding not found for this product",
        )
    return ProductEmbeddingRead(
        id=row.id,
        product_id=row.product_id,
        embedding=list(row.embedding),
        source_text=row.source_text,
        created_at=row.created_at,
    )


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
    summary="Busca semântica por texto (OpenAI)",
    description=(
        "Converte `query` em embedding (mesma API/modelo que em `/embedding/generate`) e "
        "executa a busca por similaridade no PGVector. Requer `OPENAI_API_KEY`."
    ),
)
async def semantic_search_by_text(
    body: SemanticSearchByTextBody,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[dict]:
    try:
        vector = await embed_text_openai(body.query.strip())
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
