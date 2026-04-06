"""Tarefas assíncronas executadas pelo worker ARQ."""

import structlog

log = structlog.get_logger(__name__)


async def send_welcome_email_task(ctx: dict, email: str, name: str) -> str:
    """Exemplo: envio de e-mail pós-registro (substituir por provedor real)."""
    log.info("welcome_email_queued", email=email, name=name)
    # await httpx.post(...) ou SES/SendGrid
    return "ok"


async def sample_heavy_task(ctx: dict, payload: str) -> str:
    """Processamento pesado fora da request (relatórios, reindexação, etc.)."""
    log.info("heavy_task", payload=payload)
    return "done"
