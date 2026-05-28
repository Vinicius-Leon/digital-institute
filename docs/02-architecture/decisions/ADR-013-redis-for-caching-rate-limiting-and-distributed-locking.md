# ADR-013: Redis for Caching, Rate Limiting, and Distributed Locking

- Status: Accepted
- Date: 05-11-2026
- Tags: caching, performance, infrastructure

## Context

The application has three related needs that benefit from a fast, shared in-memory store:

1. **Caching** — reducing repeated DB queries for reference data (course listings, organization config, feature flags).
2. **Rate limiting** — enforcing per-IP and per-tenant request limits across multiple API pods.
3. **Distributed locking** — preventing race conditions in critical operations (certificate issuance, idempotency key management) when running multiple worker processes.

A single tool that covers all three use cases is preferable to three separate solutions.

## Decision

Redis will be used as the shared in-memory store for all three use cases:

- **Caching:** application-layer caching using `redis-py` with TTL-based expiry. Cache keys are namespaced by tenant (`org:{id}:*`).
- **Rate limiting:** sliding window counters using Redis atomic operations (`INCR` + `EXPIRE`). Per-IP limits on public endpoints; per-tenant limits on authenticated endpoints. Response headers include `X-RateLimit-*` and `Retry-After`.
- **Distributed locking:** Redlock algorithm (or simpler single-node lock via `SET NX PX`) for short-duration locks on critical operations. Used in idempotency key management and certificate issuance.
- **JWT revocation list:** Short-lived Redis keys keyed by token JTI for immediate logout and security event revocation (see ADR-006).

Redis will run locally via Docker Compose and in production as an ElastiCache instance on AWS (or a standalone Redis on EC2 for cost-sensitive deployments).

## Consequences

**Positive:**
- Single dependency covers caching, rate limiting, and locking.
- Redis atomic operations (`INCR`, `SET NX`) are well-suited for rate limiting and locking without custom synchronization logic.
- Sub-millisecond latency for cache hits significantly reduces DB load.
- Celery already uses Redis as a result backend option (though RabbitMQ is the broker; see ADR-014).

**Negative:**
- Redis is an additional service to operate and monitor; failure affects rate limiting and caching simultaneously.
- In-memory data is volatile; Redis must not be used as a primary store for data that cannot be rebuilt from PostgreSQL.
- Redlock requires careful TTL tuning; overly short locks cause correctness issues; overly long locks cause availability issues.

**Neutral:**
- Cache invalidation strategy is explicit (key-based invalidation on write) rather than time-only TTL, to prevent serving stale data after updates.

## Alternatives Considered

**Memcached:** Covers caching only; no pub/sub, no atomic operations for rate limiting, no locking primitives. Rejected.

**In-process cache (e.g., `functools.lru_cache`):** Not shared across multiple API pods; breaks in a horizontally scaled deployment. Rejected.

**Database-backed rate limiting:** Possible but adds write load to PostgreSQL on every request. Rejected.

## Links

- Related: ADR-006 (JWT/sessions), ADR-014 (Celery+RabbitMQ), ADR-024 (idempotency), ADR-025 (feature flags)