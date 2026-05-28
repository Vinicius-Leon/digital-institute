# ADR-021: HMAC-Signed Webhooks for Outbound Events

- Status: Accepted
- Date: 05-19-2026
- Tags: webhooks, security, integrations

## Context

The platform will emit outbound webhook events to allow partner systems to react to domain events (enrollment created, certificate issued, payment received). Recipients need a way to verify that the payload originated from this system and was not tampered with in transit.

## Decision

All outbound webhooks will include an HMAC-SHA256 signature in the `X-Signature-SHA256` HTTP header (following the pattern established by GitHub and Stripe).

Implementation:
- Each webhook endpoint (registered per organization) has a unique signing secret stored in the database (encrypted at rest).
- The webhook worker (Celery task) computes `HMAC-SHA256(secret, raw_body)` and includes it in the header.
- Payload is JSON with a standard envelope: `event_type`, `event_id`, `organization_id`, `created_at`, `data`.
- Delivery includes retries with exponential backoff (3 attempts, then DLQ).
- Every delivery attempt is logged in a `webhook_deliveries` table: `event_id`, `endpoint_url`, `status_code`, `response_body`, `delivered_at`, `attempt_number`.
- Recipients verify the signature by computing the same HMAC over the raw request body and comparing with the header value using a constant-time comparison.
- A sequence diagram documenting the full flow (domain event → outbox → worker → HMAC signing → delivery → retry → DLQ) is maintained in `docs/03-api/webhooks.md`.

## Consequences

**Positive:**
- HMAC-SHA256 is a well-understood, lightweight signing mechanism that does not require PKI.
- Recipients can verify authenticity without a callback to the platform.
- The delivery audit table provides full traceability of every event.
- Pattern is familiar to developers who have integrated with GitHub or Stripe.

**Negative:**
- The signing secret must be securely communicated to the recipient at registration time and stored securely on both sides.
- HMAC does not prevent replay attacks; recipients should validate the `created_at` timestamp and use the `event_id` for idempotency.

**Neutral:**
- The platform's documentation includes a webhook verification code snippet in Python for recipient implementations.

## Alternatives Considered

**Asymmetric signatures (RSA/Ed25519):** Recipients can verify without sharing a secret, but key management is more complex. Viable for a future phase if webhook consumers are external third parties at scale.

**No signing:** Simple but provides no authenticity guarantee. Rejected.

## Links

- Related: ADR-014 (Celery), ADR-015 (outbox), ADR-024 (idempotency)