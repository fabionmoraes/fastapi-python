"""Configuração ARQ (filas Redis) para workers."""

from arq.connections import RedisSettings

from app.core.config import get_settings
from app.workers.tasks import sample_heavy_task, send_welcome_email_task


def redis_settings_for_arq() -> RedisSettings:
    settings = get_settings()
    return RedisSettings.from_dsn(str(settings.redis_url))


class WorkerSettings:
    redis_settings = redis_settings_for_arq()
    functions = [send_welcome_email_task, sample_heavy_task]
