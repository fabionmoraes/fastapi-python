"""Embedding determinístico para testar PGVector/upsert sem libs de ML (sem semântica real)."""

from __future__ import annotations

import hashlib

from app.core.config import get_settings
from app.infrastructure.embeddings.openai_embeddings import EmbeddingProviderError


def embed_text_dummy(text: str) -> list[float]:
    """
    Gera `embedding_dimensions` valores em [-1, 1] de forma determinística.
    Mesmo texto → mesma lista. Adequado para testar upsert; busca semântica não é significativa.
    """
    if not text.strip():
        raise EmbeddingProviderError("texto vazio para embedding")

    settings = get_settings()
    n = settings.embedding_dimensions
    raw = hashlib.shake_256(text.encode("utf-8")).digest(n * 2)
    out: list[float] = []
    for i in range(0, n * 2, 2):
        v = int.from_bytes(raw[i : i + 2], "big") / 65535.0 * 2.0 - 1.0
        out.append(v)
    if len(out) != n:
        raise EmbeddingProviderError("vetor dummy com tamanho incorreto")
    return out
