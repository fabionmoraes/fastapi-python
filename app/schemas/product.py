from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import DEFAULT_EMBEDDING_DIMENSIONS


def _embedding_example_vector() -> list[float]:
    """384 floats para exemplo no OpenAPI (primeiros valores ilustrativos + zeros)."""
    head = [0.012, -0.045, 0.089, -0.001, 0.0, 0.0, -0.033, 0.021]
    return head + [0.0] * (DEFAULT_EMBEDDING_DIMENSIONS - len(head))


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


class ProductDescriptionSuggestBody(BaseModel):
    """Opcional: refine a sugestão (tom, público, palavras-chave, etc.)."""

    extra_context: str | None = Field(None, max_length=4000)
    tone: str | None = Field(None, max_length=128, description="Ex.: técnico, informal, luxo")


class ProductDescriptionSuggestionRead(BaseModel):
    suggested_description: str
    model: str


class ProductMetricRead(BaseModel):
    """Um bucket (janela de tempo) na série `product_metrics`."""

    bucket: datetime
    product_id: UUID
    views: int
    revenue: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductEmbeddingRead(BaseModel):
    """Embedding persistido (PGVector). O exemplo no Swagger ilustra o formato da resposta."""

    id: UUID
    product_id: UUID
    embedding: list[float] = Field(
        ...,
        description=(
            f"Vetor com {DEFAULT_EMBEDDING_DIMENSIONS} dimensões "
            "(mesmo espaço usado na busca semântica)."
        ),
    )
    source_text: str | None = Field(
        None,
        description="Texto que foi usado para gerar o vetor (se informado no PUT).",
    )
    created_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440001",
                    "product_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                    "embedding": _embedding_example_vector(),
                    "source_text": "Notebook Pro 14 — ultrabook para produtividade.",
                    "created_at": "2026-04-06T15:30:00+00:00",
                }
            ]
        }
    )
