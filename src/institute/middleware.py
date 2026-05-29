import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from pythonjsonlogger import jsonlogger

from institute.config import get_settings

settings = get_settings()


def setup_logging() -> None:
    """Configure structured logging in JSON."""
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(settings.log_level)


async def request_id_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """
    Adds a unique request_id to each request.

    The request_id allows you to track all logs for a single request,
    even if there are hundreds of simultaneous logs from different requests.
    """
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    logger = logging.getLogger(__name__)

    start_time = time.perf_counter()

    logger.info(
        "Request started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
        },
    )

    response = await call_next(request)

    duration_ms = (time.perf_counter() - start_time) * 1000

    logger.info(
        "Request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        },
    )

    response.headers["X-Request-ID"] = request_id
    return response
