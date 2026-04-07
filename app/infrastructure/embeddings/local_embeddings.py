"""Embeddings locais com Sentence-Transformers. Instale o extra `local-embeddings`."""

from __future__ import annotations

import asyncio
from typing import Any

from app.core.config import get_settings
from app.infrastructure.embeddings.errors import EmbeddingProviderError

_model: Any = None


def _get_model() -> Any:
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise EmbeddingProviderError(
                "Sentence-Transformers não instalado. Rode: "
                'pip install -e ".[local-embeddings]"'
            ) from e
        settings = get_settings()
        _model = SentenceTransformer(settings.local_embedding_model)
    return _model


def _encode_sync(text: str) -> list[float]:
    model = _get_model()
    vec = model.encode(text, convert_to_numpy=True)
    out = [float(x) for x in vec.tolist()]
    settings = get_settings()
    if len(out) != settings.embedding_dimensions:
        raise EmbeddingProviderError(
            f"modelo retornou {len(out)} dim.; esperado {settings.embedding_dimensions}."
        )
    return out


async def embed_text_local(text: str) -> list[float]:
    if not text.strip():
        raise EmbeddingProviderError("texto vazio para embedding")
    return await asyncio.to_thread(_encode_sync, text)
