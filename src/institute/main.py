from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from institute.config import get_settings
from institute.exceptions import register_exception_handlers
from institute.middleware import request_id_middleware, setup_logging
from institute.modules.auth.router import router as auth_router
from institute.modules.health.router import router as health_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Code that runs when the application starts and stops.

    What comes before the yield runs on initialization.
    What comes after the yield runs on shutdown.
    """
    setup_logging()
    # In the future: initialize connection pools, check dependencies.
    yield
    # In the future: close connections, release resources.


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="API do Instituto Digital",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # CORS — allows browsers from different origins to access the API.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # Request_id middleware (must be added via Starlette middleware)
    app.middleware("http")(request_id_middleware)

    # Error handlers
    register_exception_handlers(app)

    # Routers
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")

    return app


app = create_app()
