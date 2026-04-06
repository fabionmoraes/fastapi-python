import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.api.routes.metrics import REQUEST_COUNT, REQUEST_LATENCY


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method
        path = (request.scope.get("path") or "/").split("?")[0][:200] or "/"
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        status_code = str(response.status_code)
        REQUEST_COUNT.labels(method=method, path=path, status=status_code).inc()
        REQUEST_LATENCY.labels(method=method, path=path).observe(elapsed)
        return response
