"""Busca por similaridade de vetores (PGVector + operador <-> L2)."""

from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import ProductEmbeddingModel


class ProductEmbeddingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_embedding(
        self,
        *,
        product_id: UUID,
        embedding: list[float],
        source_text: str | None,
    ) -> None:
        stmt = select(ProductEmbeddingModel).where(ProductEmbeddingModel.product_id == product_id)
        res = await self._session.execute(stmt)
        row = res.scalar_one_or_none()
        if row:
            row.embedding = embedding
            row.source_text = source_text
        else:
            self._session.add(
                ProductEmbeddingModel(
                    product_id=product_id,
                    embedding=embedding,
                    source_text=source_text,
                )
            )
        await self._session.flush()

    async def get_by_product_id(self, product_id: UUID) -> ProductEmbeddingModel | None:
        stmt = select(ProductEmbeddingModel).where(ProductEmbeddingModel.product_id == product_id)
        res = await self._session.execute(stmt)
        return res.scalar_one_or_none()

    async def search_similar(
        self,
        query_embedding: list[float],
        *,
        limit: int = 10,
    ) -> list[tuple[UUID, str, float]]:
        """Retorna (product_id, product_name, distância L2)."""
        vec_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        q = text(
            """
            SELECT p.id, p.name,
                   (e.embedding <-> CAST(:qv AS vector)) AS dist
            FROM product_embeddings e
            JOIN products p ON p.id = e.product_id
            ORDER BY e.embedding <-> CAST(:qv AS vector)
            LIMIT :lim
            """
        )
        result = await self._session.execute(q, {"qv": vec_str, "lim": limit})
        rows = result.all()
        return [(r[0], r[1], float(r[2])) for r in rows]
