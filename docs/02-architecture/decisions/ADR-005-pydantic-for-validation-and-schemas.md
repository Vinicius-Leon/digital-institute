# ADR-005: Pydantic for Validation and Schemas

- Status: Accepted
- Date: 05-03-2026
- Tags: validation, schemas, api

## Context

Every API endpoint requires request validation and response serialization. Validation logic needs to be explicit, type-safe, and reusable across the codebase. Additionally, application settings loaded from environment variables need a structured, validated representation.

## Decision

Pydantic v2 will be used as the single library for:
1. **API schemas** — request bodies, response models, and query parameter models, used directly as FastAPI type annotations.
2. **Settings management** — `pydantic-settings` for environment variable loading, with per-environment overrides.
3. **Internal DTOs** — data transfer objects passed between service and controller layers.

SQLAlchemy ORM models and Pydantic schemas will remain separate classes. ORM models represent database rows; Pydantic models represent API contracts. Explicit mapping between them is the responsibility of the service layer.

## Consequences

**Positive:**
- FastAPI is built around Pydantic; the integration is seamless and requires no adapter code.
- Validation errors are automatically converted to structured 422 responses.
- Pydantic v2 is significantly faster than v1 due to the Rust-based core.
- Settings validation catches missing environment variables at startup rather than at runtime.
- Type annotations on Pydantic models are understood by mypy, enabling static type checking across schema boundaries.

**Negative:**
- Maintaining separate ORM and Pydantic models requires explicit mapping code. This is a deliberate tradeoff for keeping API contracts decoupled from the database schema.
- Pydantic v2 introduced breaking changes from v1; any third-party libraries that still use v1 internally may require compatibility wrappers.

**Neutral:**
- JSON serialization of responses uses Pydantic's `.model_dump(mode="json")` to ensure consistent handling of dates, UUIDs, and decimals.

## Alternatives Considered

**Marshmallow:** Mature but verbose, not natively integrated with FastAPI, and slower than Pydantic v2.

**Dataclasses:** Supported by FastAPI but lack validators, field-level constraints, and settings management; would require a separate validation library.

## Links

- Related: ADR-003 (Python), ADR-004 (FastAPI), ADR-009 (SQLAlchemy)