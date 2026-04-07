"""Geração de texto via SDK oficial `google-genai` (`generate_content`)."""

import asyncio

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.core.config import get_settings
from app.infrastructure.embeddings.errors import EmbeddingProviderError
from app.infrastructure.gemini.http_error import raise_from_genai_sdk_error


class GeminiTextError(Exception):
    pass

def _sync_generate_text(
    *,
    api_key: str,
    model: str,
    user_prompt: str,
    system_instruction: str | None,
) -> str:
    client = genai.Client(api_key=api_key)
    cfg_kwargs: dict = {
        "temperature": 0.7,
        "max_output_tokens": 4096,
    }
    if system_instruction and system_instruction.strip():
        cfg_kwargs["system_instruction"] = system_instruction.strip()
    config = types.GenerateContentConfig(**cfg_kwargs)
    
    response = client.models.generate_content(
        model=model,
        contents=user_prompt,
        config=config,
    )
    text = (response.text or "").strip()
    if not text:
        raise GeminiTextError("Gemini retornou texto vazio (candidates ou bloqueio de segurança).")
    return text


async def gemini_generate_text(
    *,
    user_prompt: str,
    system_instruction: str | None = None,
) -> str:
    settings = get_settings()
    key = settings.gemini_api_key
    if not key or not key.strip():
        raise EmbeddingProviderError(
            "GEMINI_API_KEY não configurada. Obtenha em https://aistudio.google.com/apikey"
        )

    model = settings.gemini_text_model.strip()
    try:
        return await asyncio.to_thread(
            _sync_generate_text,
            api_key=key.strip(),
            model=model,
            user_prompt=user_prompt,
            system_instruction=system_instruction,
        )
    except GeminiTextError:
        raise
    except genai_errors.APIError as e:
        raise_from_genai_sdk_error(e, operation="generate_content")
    except Exception as e:
        raise_from_genai_sdk_error(e, operation="generate_content")
