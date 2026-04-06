from contextlib import asynccontextmanager

from arq import create_pool
from fastapi import FastAPI

from app.api.middleware.prometheus import PrometheusMiddleware
from app.api.routes import auth, clients, metrics, products, users
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.infrastructure.messaging.arq_settings import redis_settings_for_arq


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    app.state.arq_pool = await create_pool(redis_settings_for_arq())
    yield
    await app.state.arq_pool.close()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(PrometheusMiddleware)

    app.include_router(metrics.router)
    app.include_router(auth.router, prefix=settings.api_prefix)
    app.include_router(users.router, prefix=settings.api_prefix)
    app.include_router(products.router, prefix=settings.api_prefix)
    app.include_router(clients.router, prefix=settings.api_prefix)

    return app


app = create_app()
