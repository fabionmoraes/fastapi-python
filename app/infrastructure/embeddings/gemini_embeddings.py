"""Embeddings via SDK oficial `google-genai` (`embed_content`)."""

import asyncio
import math

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.core.config import get_settings
from app.infrastructure.embeddings.errors import EmbeddingProviderError
from app.infrastructure.gemini.http_error import raise_from_genai_sdk_error


def _l2_normalize(vec: list[float]) -> list[float]:
    s = math.sqrt(sum(x * x for x in vec))
    if s <= 0:
        return vec
    return [x / s for x in vec]


def _sync_embed_text(
    text: str,
    *,
    api_key: str,
    model: str,
    dim: int,
) -> list[float]:
    client = genai.Client(api_key=api_key)

    def call(output_dimensionality: int) -> list[float]:
        cfg = types.EmbedContentConfig(output_dimensionality=output_dimensionality)
        r = client.models.embed_content(model=model, contents=text, config=cfg)
        vals = r.embeddings[0].values
        return [float(x) for x in vals]

    try:
        vec = call(dim)
    except genai_errors.ClientError as e:
        if e.code == 400 and dim != 768:
            try:
                vec = call(768)
            except genai_errors.APIError as e2:
                raise_from_genai_sdk_error(e2, operation="embed_content")
        else:
            raise_from_genai_sdk_error(e, operation="embed_content")
    except genai_errors.ServerError as e:
        raise_from_genai_sdk_error(e, operation="embed_content")

    if len(vec) == dim:
        return _l2_normalize(vec)
    if len(vec) > dim:
        return _l2_normalize(vec[:dim])
    raise EmbeddingProviderError(
        f"dimensão do vetor Gemini ({len(vec)}) < embedding_dimensions ({dim})"
    )


async def embed_text_gemini(text: str) -> list[float]:
    """
    Usa `output_dimensionality` alinhado a `Settings.embedding_dimensions` (ex.: 384).
    Se a API rejeitar o tamanho, tenta 768 e trunca para `embedding_dimensions` + L2.
    """
    settings = get_settings()
    key = settings.gemini_api_key
    if not key or not key.strip():
        raise EmbeddingProviderError(
            "GEMINI_API_KEY não configurada. Obtenha em https://aistudio.google.com/apikey "
            "ou use outro EMBEDDING_PROVIDER."
        )

    model = settings.gemini_embedding_model.strip()
    dim = settings.embedding_dimensions

    try:
        return await asyncio.to_thread(
            _sync_embed_text,
            text,
            api_key=key.strip(),
            model=model,
            dim=dim,
        )
    except EmbeddingProviderError:
        raise
    except Exception as e:
        raise_from_genai_sdk_error(e, operation="embed_content")
