# ADR-004: FastAPI as API Framework

- Status: Accepted
- Date: 05-02-2026
- Tags: api, framework, foundation

## Context

The system requires an HTTP API framework capable of handling both synchronous and asynchronous endpoints, generating OpenAPI documentation automatically, and integrating cleanly with Pydantic for request/response validation.

The framework will be used across the entire API surface: public pages (via Jinja2 templates), REST endpoints for the mobile/JS clients, and internal endpoints consumed by workers and integrations.

## Decision

FastAPI will be the API framework. It will run on Uvicorn (development) and Gunicorn with Uvicorn workers (production), following the ASGI standard.

Key usage patterns:
- All request bodies and response models defined as Pydantic schemas.
- Async route handlers for I/O-bound operations; sync handlers only where blocking libraries make async impractical.
- Dependency injection via FastAPI's `Depends` mechanism for authentication, database sessions, and tenant context.
- OpenAPI spec auto-generated and kept clean as a public contract artifact.
- Jinja2 templating for server-rendered public pages.

## Consequences

**Positive:**
- Automatic OpenAPI/Swagger documentation reduces manual documentation burden and serves as a living contract.
- Native async/await support enables high-concurrency I/O with a small number of threads.
- Pydantic integration is first-class; validation errors are automatically serialized into structured HTTP 422 responses.
- Dependency injection is clean, testable, and composable.
- Active community, frequent releases, and strong production adoption.

**Negative:**
- Async pitfalls (running blocking code in async handlers) must be guarded against through code review and linting conventions.
- Jinja2 integration is functional but less opinionated than dedicated server-rendered frameworks (Django); discipline is needed to keep template logic thin.

**Neutral:**
- API versioning under `/api/v1/` is enforced from the Prototype phase, allowing future version routes to coexist without breaking changes.

## Alternatives Considered

**Django REST Framework:** Mature and batteries-included, but synchronous by default, less ergonomic for async, and the ORM would conflict with the SQLAlchemy decision (ADR-009).

**Flask:** Simpler but lacks native async, requires manual OpenAPI integration, and has no built-in dependency injection.

**Litestar:** Promising but smaller community and ecosystem compared to FastAPI at the time of this decision.

## Links

- Related: ADR-003 (Python), ADR-005 (Pydantic), ADR-006 (JWT auth),
  ADR-009 (SQLAlchemy)