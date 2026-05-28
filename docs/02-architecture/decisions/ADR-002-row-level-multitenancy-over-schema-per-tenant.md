# ADR-002: Row-Level Multi-Tenancy over Schema-per-Tenant

- Status: Accepted
- Date: 04-30-2026
- Tags: architecture, multi-tenancy, database

## Context

The platform must serve multiple organizations (Instituto units, partner organizations, or independent deployments) from a single running instance. Data from different organizations must be strictly isolated: Org A must never be able to read or write Org B's data.

There are three common multi-tenancy models in relational databases:

1. **Separate databases per tenant** — strongest isolation, highest operational cost.
2. **Schema per tenant** — strong isolation within one database, but requires dynamic schema management and complicates migrations.
3. **Shared schema with a tenant discriminator column** — simplest to operate, requires disciplined query filtering.

At this stage, the number of tenants is small and the engineering team cannot afford the operational overhead of managing N schemas or N databases.

## Decision

We will use a shared schema (row-level) multi-tenancy model. Every business entity table will include an `organization_id` foreign key column. All application-layer queries must filter by `organization_id` explicitly.

To prevent accidental data leakage:
- A base repository class will enforce `organization_id` filtering on all queries by default.
- At least one automated integration test per release will assert that a request authenticated as Org A cannot retrieve, modify, or delete Org B's resources.
- PostgreSQL row-level security (RLS) may be introduced as an additional safeguard in a future iteration.

## Consequences

**Positive:**
- Single schema means Alembic migrations apply once and cover all tenants immediately.
- Simpler connection pooling: one pool serves all tenants.
- No dynamic schema creation or teardown logic required.
- Operational simplicity: backup, restore, and monitoring cover all tenants uniformly.

**Negative:**
- Isolation is enforced at the application layer; a bug in query construction could expose cross-tenant data if not caught by tests.
- A large tenant's data volume lives in shared tables, which may require careful indexing (composite indexes on `organization_id` + entity-specific columns).
- Regulatory requirements demanding physical data separation (e.g., specific LGPD interpretations) cannot be satisfied without architectural changes.

**Neutral:**
- All indexes on business tables will be created with `organization_id` as the leading column to maintain query performance per tenant.
- Feature flags and rate limits are also scoped per organization (see ADR-025), which aligns naturally with this model.

## Alternatives Considered

**Schema per tenant:** Rejected due to complexity in migration management (Alembic would need to run against each schema independently), connection pooling complications, and high operational overhead for a small team.

**Database per tenant:** Rejected for the same operational reasons, amplified. Suitable for a future phase if a specific tenant requires contractual data isolation.

## Links

- Related: ADR-001 (modular monolith), ADR-008 (PostgreSQL), ADR-016 (RBAC),
  ADR-025 (feature flags)