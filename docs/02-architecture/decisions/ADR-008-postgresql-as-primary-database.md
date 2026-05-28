# ADR-008: PostgreSQL as Primary Database

- Status: Accepted
- Date: 05-06-2026
- Tags: database, foundation

## Context

The platform requires a relational database capable of handling transactional business data (enrollments, attendance, certificates, payments), full-text search, vector embeddings, and complex reporting queries. The database must support multi-tenant row filtering, foreign key constraints, and ACID
transactions.

The managed deployment target is AWS RDS, which supports PostgreSQL natively.

## Decision

PostgreSQL (14+) will be the sole primary database for all application data. It will run locally via Docker Compose and in production via AWS RDS for PostgreSQL.

PostgreSQL features leveraged across the project:
- ACID transactions with `SERIALIZABLE` isolation where required.
- Row-level security (RLS) as a future hardening layer for multi-tenancy.
- Full-text search via `tsvector`/`tsquery` (see ADR-011), eliminating the need for a separate search engine in the initial phases.
- `pgvector` extension for semantic search embeddings (see ADR-012).
- `JSONB` for semi-structured data where a rigid schema would be premature.
- Composite indexes, partial indexes, and `EXPLAIN ANALYZE` for query tuning.

## Consequences

**Positive:**
- Single data store for transactional, search, and vector workloads reduces operational surface area.
- AWS RDS provides managed backups, failover (Multi-AZ), and point-in-time recovery without custom tooling.
- Mature ecosystem: SQLAlchemy, Alembic, pgvector, and most Python libraries have first-class PostgreSQL support.
- Strong consistency model simplifies reasoning about multi-tenant data isolation.

**Negative:**
- As data volume and query complexity grow, full-text search and vector search within Postgres may hit performance ceilings that a dedicated engine (Elasticsearch, Pinecone) would not. This is an accepted risk for the current scale.
- Schema migrations require careful management (Alembic + expand/contract strategy in production).

**Neutral:**
- Redis is used alongside PostgreSQL for caching and rate limiting (see ADR-013), not as a replacement for any relational data.

## Alternatives Considered

**MySQL/MariaDB:** Lacks native full-text search quality, has weaker JSON support, and does not support `pgvector`. Rejected.

**MongoDB:** Document model does not align with the strongly relational domain (foreign keys, enrollment states, audit logs). Rejected.

**CockroachDB:** Distributed SQL for global deployments, but operationally complex and not required at this scale. Rejected.

## Links

- Related: ADR-002 (multi-tenancy), ADR-009 (SQLAlchemy), ADR-010 (Alembic), ADR-011 (FTS), ADR-012 (pgvector)