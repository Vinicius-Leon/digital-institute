# ADR-024: Idempotency Key Pattern for Critical Operations

- Status: Accepted
- Date: 05-22-2026
- Tags: reliability, payments, messaging, api

## Context

Distributed systems must handle network failures, client retries, and worker restarts gracefully. Without idempotency controls, the following failure modes cause real harm: a student receives two enrollment confirmation emails; a certificate is issued twice; a charge is processed twice because the client retried after a timeout.

Idempotency must be enforced at the application layer for operations where duplicate execution has observable side effects.

## Decision

I will implement the Idempotency Key pattern for all critical write operations.

Covered operations (minimum):
- Certificate issuance
- Email notification dispatch
- Stripe charge creation
- Outbound webhook delivery
- QR code check-in

Implementation:
- Clients send an `Idempotency-Key` header (UUID v4) with requests to critical endpoints. The API documents which endpoints require or accept this header.
- On receiving a request with an `Idempotency-Key`, the application checks a Redis store (with TTL of 24 hours) for an existing result for that key.
  - If found: return the stored response immediately without re-executing.
  - If not found: execute the operation, store the result keyed by `(organization_id, endpoint, idempotency_key)`, and return the response.
- For Celery tasks, the idempotency key is passed as a task argument. The task checks the key before executing and records completion atomically.
- For Stripe API calls, the `Idempotency-Key` is forwarded directly to Stripe's API, which provides its own idempotency guarantee for charge creation.
- Idempotency keys older than 24 hours are expired via a scheduled Celery cron job (v3).
- The QR code check-in flow uses a composite idempotency key of `(student_id, lesson_id, date)` to prevent replay attacks within the check-in window.

## Consequences

**Positive:**
- Safe retries: clients and workers can retry failed requests without risk of duplicate side effects.
- Aligns with at-least-once delivery semantics from the outbox pattern (ADR-015); consumers must be idempotent, and this pattern provides the mechanism.
- Stripe's native idempotency key support makes the integration straightforward.

**Negative:**
- Redis dependency for idempotency key storage: if Redis is unavailable, the system can either reject critical operations (safe but unavailable) or proceed without idempotency checks (available but unsafe). The current policy is to reject and return a 503, documented in the incident runbook.
- 24-hour key TTL is a business decision; shorter TTLs reduce storage but increase the window where duplicate requests are not detected.

**Neutral:**
- The `Idempotency-Key` API is documented in `docs/03-api/idempotency.md` with request/response examples and retry behavior.

## Alternatives Considered

**Database-backed idempotency store:** More durable than Redis but slower and adds write load to PostgreSQL on every critical operation. Redis TTL-based expiry is simpler and sufficient.

**No idempotency (rely on client discipline):** Insufficient for a payment and certificate system where duplicates cause real user harm. Rejected.

## Links

- Related: ADR-013 (Redis), ADR-014 (Celery), ADR-015 (outbox), ADR-019 (Stripe), ADR-021 (webhooks)