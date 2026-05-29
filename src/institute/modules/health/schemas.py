from pydantic import BaseModel


class DependencyStatus(BaseModel):
    status: str  # "ok" | "degraded" | "unavailable"
    latency_ms: float | None = None
    detail: str | None = None


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    dependencies: dict[str, DependencyStatus]
