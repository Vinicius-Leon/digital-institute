# ADR-009: SQLAlchemy 2 with ORM and Core

- Status: Accepted
- Date: 05-07-2026
- Tags: database, orm, foundation

## Context

The application needs a database access layer that supports both high-level object mapping (for domain entities) and low-level query construction (for complex reporting and bulk operations). The layer must work with async drivers to align with FastAPI's async model.

## Decision

SQLAlchemy 2.x will be used as the database access library, with both the ORM and Core APIs available and used according to context:

- **ORM** (`DeclarativeBase`, `relationship`, `Session`) for standard CRUD operations on domain entities, where the object graph maps cleanly to domain models.
- **Core** (`select`, `update`, `delete`, `text`) for complex queries, bulk operations, reporting, and cases where the ORM abstraction adds unnecessary overhead.
- **Async support** via `asyncpg` driver and `AsyncSession` for all application-layer database interactions.
- **Sync sessions** via `psycopg2` for Alembic migrations and scripts that do not run in the async context.

All database sessions will be managed through FastAPI's dependency injection (`Depends(get_db)`), ensuring sessions are scoped to the request lifecycle.

Connection pooling is configured via SQLAlchemy's built-in pool, tuned for the expected concurrency of the deployment environment.

## Consequences

**Positive:**
- SQLAlchemy 2's unified API is significantly cleaner than 1.x; the 2.0 query style (`select(Model).where(...)`) is explicit and type-checker-friendly.
- Using Core for complex queries avoids the N+1 problems that ORM relationships can introduce if not managed carefully.
- `asyncpg` is one of the fastest PostgreSQL drivers available for Python.
- The repository pattern built on top of SQLAlchemy keeps business logic independent of the ORM details.

**Negative:**
- Using both ORM and Core requires discipline regarding when to use each one; mixing patterns in the same query can produce unexpected behavior.
- Async SQLAlchemy has subtleties (lazy loading does not work in async context; all relationships must be explicitly eager-loaded or accessed synchronously).

**Neutral:**
- ORM models are kept strictly separate from Pydantic schemas (see ADR-005). Mapping between them is done in the service layer.

## Alternatives Considered

**SQLAlchemy 1.x:** Older API style, lacks the clean 2.0 query syntax and first-class async support. Rejected in favor of the current stable 2.x.

**Tortoise ORM / SQLModel:** Smaller ecosystems, less mature async support, and fewer production references. SQLAlchemy's depth and stability are preferred.

**Raw SQL with asyncpg:** Maximum control but no schema introspection, no migration integration, and significant boilerplate. Acceptable for hotspot queries via Core's `text()`, not as the primary access pattern.

## Links

- Related: ADR-008 (PostgreSQL), ADR-010 (Alembic), ADR-005 (Pydantic)