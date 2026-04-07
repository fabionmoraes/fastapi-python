"""Tratamento de erros da API Gemini (REST legado ou SDK `google-genai`)."""

import json
import re

from app.infrastructure.embeddings.errors import EmbeddingProviderError, GeminiRateLimitError

_RETRY = re.compile(r"Please retry in ([\d.]+)s", re.I)


def parse_retry_after_seconds(response_text: str) -> float | None:
    try:
        data = json.loads(response_text)
        msg = (data.get("error") or {}).get("message") or ""
    except (json.JSONDecodeError, TypeError, AttributeError):
        msg = response_text
    m = _RETRY.search(msg)
    return float(m.group(1)) if m else None


def raise_from_genai_sdk_error(exc: BaseException, *, operation: str) -> None:
    """Mapeia exceções do pacote `google-genai`; sempre lança."""
    from google.genai import errors as genai_errors

    if isinstance(exc, genai_errors.ClientError):
        if exc.code == 429:
            raw = json.dumps(exc.details) if exc.details else str(exc)
            retry = parse_retry_after_seconds(raw)
            snippet = str(exc)[:1200]
            msg = (
                "Limite de quota do Gemini atingido (HTTP 429: free tier ou rate limit). "
                "Aguarde alguns minutos ou defina outro modelo no .env, por exemplo "
                "GEMINI_TEXT_MODEL=gemini-2.5-flash-lite ou gemini-3-flash-preview. "
                "Documentação: https://ai.google.dev/gemini-api/docs/rate-limits — "
                f"Resposta: {snippet}"
            )
            raise GeminiRateLimitError(msg, retry_after_seconds=retry) from exc
        raise EmbeddingProviderError(
            f"Gemini {operation} HTTP {exc.code}: {str(exc)[:1200]}"
        ) from exc
    if isinstance(exc, genai_errors.ServerError):
        raise EmbeddingProviderError(
            f"Gemini {operation} (erro no servidor): {str(exc)[:1200]}"
        ) from exc
    raise EmbeddingProviderError(f"Gemini {operation}: {str(exc)[:1200]}") from exc
