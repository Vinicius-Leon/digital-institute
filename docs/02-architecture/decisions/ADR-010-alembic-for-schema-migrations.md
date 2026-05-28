# ADR-010: Alembic for Schema Migrations

- Status: Accepted
- Date: 05-08-2026
- Tags: database, migrations

## Context

Database schema changes are inevitable as the product evolves. Migrations must be version-controlled, reproducible across environments (local, staging, production), and safe to run in a CI/CD pipeline without manual intervention.

## Decision

Alembic will be used as the schema migration tool, integrated with SQLAlchemy.

Migration conventions:
- **Auto-generation** (`alembic revision --autogenerate`) is used as a starting point; all generated migrations are reviewed and edited before commit.
- **Sequential numbering** with descriptive names (e.g., `0012_add_certificate_revocation_reason.py`).
- **Expand/contract pattern** for production changes that could lock tables or break running application code:
  1. Expand: add the new column/index (nullable, with default).
  2. Deploy the new application version.
  3. Contract: remove old columns/constraints in a subsequent migration.
- **Migration tests** in CI: migrations are applied from zero on a clean database in every CI run, followed by `alembic downgrade -1` to verify reversibility where applicable.
- In Kubernetes deployments, migrations run as an init container or a dedicated Job before the API pods start (see v4 deploy runbook).

## Consequences

**Positive:**
- Migrations are code: reviewed in PRs, versioned in git, and auditable.
- Auto-generation from SQLAlchemy models reduces manual SQL error risk.
- Alembic's `--autogenerate` detects most common schema drifts.
- Init container pattern ensures migrations complete before traffic reaches the new API version.

**Negative:**
- Auto-generated migrations can miss certain changes (custom types, check constraints, index options); manual review is mandatory.
- The expand/contract pattern adds deployment ceremony for breaking schema changes, which is the correct trade-off for production safety.

**Neutral:**
- A `alembic current` / `alembic history` check is included in the /health endpoint response to surface migration state in production.

## Alternatives Considered

**Flyway / Liquibase:** JVM-based tools with strong SQL-first support, but they require a separate runtime and are not integrated with SQLAlchemy's model introspection.

**Django migrations:** Not applicable outside the Django ecosystem.

**Manual SQL scripts:** No version tracking, no rollback support, no CI integration. Rejected.

## Links

- Related: ADR-008 (PostgreSQL), ADR-009 (SQLAlchemy)