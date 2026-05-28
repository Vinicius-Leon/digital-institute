# ADR-015: Outbox Pattern for Reliable Event Delivery

- Status: Accepted
- Date: 05-13-2026
- Tags: reliability, messaging, events

## Context

Several domain operations (certificate issuance, enrollment confirmation, payment received) must reliably trigger downstream effects (sending emails, delivering webhooks, updating read models). A naive implementation publishes a message to RabbitMQ inside the same request handler that commits the database transaction. If the message publish succeeds but the DB commit fails (or vice versa), the system ends up in an inconsistent state.

The outbox pattern solves this by treating event publishing as part of the database transaction.

## Decision

I will implement the transactional outbox pattern for all domain events that require reliable downstream delivery.

Implementation:
1. An `outbox_events` table in PostgreSQL stores pending events as part of the same database transaction that modifies domain state. If the transaction rolls back, the event is never persisted.
2. A Celery periodic task (or a dedicated poller) reads unprocessed events from the outbox table and publishes them to RabbitMQ.
3. Events are marked as `processed` (with timestamp) after successful publish.
4. Failed publish attempts are retried with backoff; events that fail repeatedly are flagged for manual review.
5. The `outbox_events` table includes: `id`, `aggregate_type`, `aggregate_id`, `event_type`, `payload` (JSONB), `created_at`, `processed_at`, `attempts`, `last_error`.

This pattern guarantees **at-least-once delivery**; consumers (webhook handler, email worker) must be idempotent (see ADR-024).

## Consequences

**Positive:**
- Atomicity: domain state change and event creation either both commit or both roll back.
- No message loss due to broker unavailability at the time of the transaction; events are durably stored in PostgreSQL until delivered.
- Decouples the business transaction from the messaging infrastructure.

**Negative:**
- Adds a polling component (or change data capture) to the architecture.
- Outbox table must be cleaned up periodically (cron job in v3) to prevent unbounded growth.
- At-least-once delivery requires all consumers to handle duplicate events correctly.

**Neutral:**
- A sequence diagram documenting the full outbox-to-delivery flow (including retry and DLQ) is produced in v3 and referenced in the webhook API documentation.

## Alternatives Considered

**Publish directly in the request handler:** Simple but risks publish-without-commit or commit-without-publish inconsistencies. Rejected.

**Change Data Capture (CDC) with Debezium:** Elegant but requires Kafka and Debezium infrastructure. Overly complex for the current scale. May be introduced in a future phase if event volume warrants it.

## Links

- Related: ADR-014 (Celery+RabbitMQ), ADR-021 (webhooks), ADR-024 (idempotency)