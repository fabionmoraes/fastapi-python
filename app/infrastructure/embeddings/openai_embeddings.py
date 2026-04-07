"""Embeddings via API OpenAI (modelos text-embedding-3-* com parâmetro `dimensions`)."""

import httpx

from app.core.config import get_settings
from app.infrastructure.embeddings.errors import EmbeddingProviderError


async def embed_text_openai(text: str) -> list[float]:
    """
    Gera vetor de embedding alinhado a `Settings.embedding_dimensions` (ex.: 384).

    Requer `OPENAI_API_KEY`. Usa `text-embedding-3-small` por padrão (barato e
    compatível com `dimensions` menor que o tamanho nativo do modelo).
    """
    settings = get_settings()
    key = settings.openai_api_key
    if not key or not key.strip():
        raise EmbeddingProviderError(
            "OPENAI_API_KEY não configurada. Defina no .env ou use PUT .../embedding "
            "com um vetor gerado externamente."
        )

    payload = {
        "model": settings.openai_embedding_model,
        "input": text,
        "dimensions": settings.embedding_dimensions,
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    url = f"{settings.openai_base_url.rstrip('/')}/embeddings"

    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(url, json=payload, headers=headers)

    if r.status_code != 200:
        detail = r.text[:500] if r.text else r.reason_phrase
        raise EmbeddingProviderError(f"OpenAI embeddings HTTP {r.status_code}: {detail}")

    data = r.json()
    try:
        vec = data["data"][0]["embedding"]
    except (KeyError, IndexError) as e:
        raise EmbeddingProviderError(f"resposta OpenAI inesperada: {data!r}") from e

    if len(vec) != settings.embedding_dimensions:
        ed = settings.embedding_dimensions
        raise EmbeddingProviderError(
            f"dimensão do vetor ({len(vec)}) != embedding_dimensions ({ed})"
        )
    return [float(x) for x in vec]
