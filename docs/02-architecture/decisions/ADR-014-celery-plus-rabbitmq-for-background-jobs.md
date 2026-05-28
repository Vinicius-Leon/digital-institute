# ADR-014: Celery + RabbitMQ for Background Jobs

- Status: Accepted
- Date: 05-12-2026
- Tags: messaging, background-jobs, reliability

## Context

The platform has multiple operations that must not block the HTTP request cycle: sending emails, issuing certificates, processing webhook deliveries, running scheduled reports, and handling media pipelines. These tasks also require retry logic, dead-letter queues, and visibility into failures.

Two components are needed: a message broker (to transport task messages) and a task framework (to execute, retry, and monitor tasks).

## Decision

Celery will be used as the task framework and RabbitMQ as the message broker.

Architecture:
- **RabbitMQ** handles message persistence, routing (via exchanges and queues), and dead-letter routing (DLQ via `x-dead-letter-exchange`).
- **Celery** handles task definition, worker execution, retry policies (exponential backoff with jitter), and task state tracking.
- A dedicated DLQ queue receives tasks that have exhausted all retries; an administrative endpoint (v3) allows DLQ inspection and reprocessing.
- Task idempotency is enforced at the application level (see ADR-024), not relied upon from the broker.
- Scheduled tasks (cron-like) are managed via Celery Beat.
- Workers run as a separate process/container (`worker` service in Docker Compose and a separate Deployment in Kubernetes).

Primary task categories:
- Email notifications (Celery + SES, see ADR-018).
- Certificate issuance (idempotent, see ADR-024).
- Webhook delivery (HMAC signed, see ADR-021).
- Scheduled cleanup jobs (token expiry, old idempotency keys).
- Media pipeline (thumbnail/image optimization, v5).
- ETL coordination (Airflow handles pipelines, but lightweight pre-processing jobs run in Celery).

## Consequences

**Positive:**
- RabbitMQ's AMQP protocol provides reliable message delivery with acknowledgments; unacknowledged messages are requeued on worker failure.
- DLQ support is native in RabbitMQ, making failure management explicit rather than implicit.
- Celery is the most widely deployed Python task framework with extensive documentation and production references.
- Separation of the worker process from the API process allows independent scaling of background workloads.

**Negative:**
- RabbitMQ adds operational complexity: cluster management, queue monitoring, and connection pool tuning.
- Celery's configuration surface is large; incorrect settings (acks_late, prefetch_count) can cause subtle message loss or duplication.
- Debugging failed tasks requires access to Flower (Celery monitoring) or the DLQ endpoint.

**Neutral:**
- Redis is available as a Celery result backend (for task state queries) but RabbitMQ is the broker. This is a deliberate split: RabbitMQ for durability, Redis for fast state lookups.

## Alternatives Considered

**Celery + Redis (as broker):** Redis-as-broker is simpler to operate but provides weaker delivery guarantees (no AMQP, limited DLQ support). Rejected in favor of RabbitMQ for production reliability.

**Dramatiq + RabbitMQ:** Cleaner API than Celery, but smaller community and ecosystem. Celery's maturity and reference implementations outweigh Dramatiq's ergonomic advantages.

**Temporal:** Excellent workflow durability but operationally heavy for the current team size and phase. Rejected.

## Links

- Related: ADR-013 (Redis), ADR-015 (outbox), ADR-018 (SES), ADR-021 (webhooks), ADR-024 (idempotency)