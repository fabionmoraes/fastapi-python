"""Escolhe o provedor de embedding: dummy (teste), local (Sentence-Transformers) ou OpenAI."""

from typing import Literal

from app.core.config import get_settings
from app.infrastructure.embeddings.dummy_embeddings import embed_text_dummy
from app.infrastructure.embeddings.local_embeddings import embed_text_local
from app.infrastructure.embeddings.openai_embeddings import embed_text_openai


async def embed_text(text: str) -> list[float]:
    settings = get_settings()
    provider: Literal["dummy", "local", "openai"] = settings.embedding_provider
    if provider == "openai":
        return await embed_text_openai(text)
    if provider == "local":
        return await embed_text_local(text)
    return embed_text_dummy(text)
