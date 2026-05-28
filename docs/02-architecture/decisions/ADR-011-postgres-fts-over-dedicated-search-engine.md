# ADR-011: Postgres FTS over Dedicated Search Engine

- Status: Accepted
- Date: 05-09-2026
- Tags: search, database, performance

## Context

The platform requires full-text search over courses, blog posts, and materials. Dedicated search engines (Elasticsearch, OpenSearch, Typesense, Meilisearch) offer advanced relevance tuning, faceting, and horizontal scalability, but introduce a separate operational component that must be kept in sync with the primary database.

At the current scale and team size, the cost of operating a dedicated search engine outweighs its benefits.

## Decision

We will use PostgreSQL's native full-text search (`tsvector`, `tsquery`, `GIN` indexes, `ts_rank`) for all search functionality in the initial phases (up to and including v3).

Implementation details:
- `tsvector` columns are maintained via triggers or application-layer updates on insert/update.
- `GIN` indexes on `tsvector` columns for efficient full-text queries.
- `plainto_tsquery` and `websearch_to_tsquery` for user-facing search input parsing.
- Portuguese language configuration (`'portuguese'`) for proper stemming and stop-word handling.
- Search results include `ts_rank` for relevance ordering.

The decision to migrate to a dedicated search engine will be revisited if search query latency exceeds acceptable thresholds under production load.

## Consequences

**Positive:**
- Zero additional infrastructure: search queries run in the same database already in use.
- No synchronization pipeline between primary DB and search index.
- GIN-indexed `tsvector` queries are fast for datasets up to millions of rows.
- Simplifies the operational model significantly.

**Negative:**
- FTS is less powerful than Elasticsearch for faceted search, typo tolerance, and complex relevance tuning.
- Portuguese stemming in Postgres is adequate but not as refined as Elasticsearch's analysis pipeline.
- As data volume grows, full-text queries compete for I/O with transactional queries on the same server.

**Neutral:**
- Semantic (vector) search is handled separately via pgvector (ADR-012) an does not replace keyword FTS but complements it in the v6 RAG feature.

## Alternatives Considered

**Elasticsearch / OpenSearch:** Powerful but operationally heavy. Requires a sync pipeline, additional AWS instance or managed service cost, and operational expertise. Rejected for the current scale.

**Typesense / Meilisearch:** Simpler than Elasticsearch but still require a separate service and sync. Rejected for the same reasons.

## Links

- Related: ADR-008 (PostgreSQL), ADR-012 (pgvector)