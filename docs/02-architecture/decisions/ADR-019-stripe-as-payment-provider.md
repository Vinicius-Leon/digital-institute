# ADR-019: Stripe as Payment Provider

- Status: Accepted
- Date: 05-17-2026
- Tags: payments, integrations, security

## Context

The v5 phase introduces one-time and recurring donations. The payment integration must handle card processing securely (PCI-DSS compliance), support recurring billing, provide webhook notifications for asynchronous payment events, and integrate with financial reconciliation workflows.

## Decision

Stripe will be the payment provider for all monetary transactions.

Integration architecture:
- **Stripe Elements / Payment Intents API** for client-side card collection, keeping raw card data out of the application's scope (PCI-DSS SAQ A).
- **Stripe Subscriptions** for recurring donations.
- **Stripe Webhooks** for asynchronous event notification (payment succeeded, subscription canceled, refund processed). Webhook payloads are verified using the Stripe webhook secret signature before processing.
- **Idempotency-Key** header is sent on all Stripe API calls that create charges or refunds (see ADR-024), preventing duplicate charges on retry.
- A local `payments` and `stripe_events` table tracks the application's view of payment state for reconciliation.
- **Reconciliation jobs** (Celery, scheduled) compare local records against the Stripe balance transactions API and flag discrepancies.
- Refunds and chargebacks follow an audited flow: request → approval → execution, with each step recorded in the audit log.

## Consequences

**Positive:**
- Stripe is the de facto standard for SaaS payment integration; extensive documentation, well-maintained Python SDK (`stripe`), and a robust sandbox.
- Stripe Elements keeps the application out of PCI-DSS scope for card data.
- Webhook event model aligns naturally with the outbox/reliable delivery pattern (ADR-015).
- Idempotent Stripe API prevents double-charges on network retries.

**Negative:**
- Stripe fees apply per transaction; the organization must account for this in financial modeling.
- Webhook processing must be idempotent (Stripe may deliver the same event more than once).
- Reconciliation logic must handle Stripe's eventual consistency (events may arrive out of order).

**Neutral:**
- All Stripe interactions are encapsulated in a `PaymentService`; replacing Stripe with another provider in the future would require reimplementing that service, not changes to the domain layer.

## Alternatives Considered

**PayPal:** Lower developer experience quality and less suitable for modern SaaS subscription billing. Rejected.

**MercadoPago:** Relevant for Brazilian market, but Stripe's global infrastructure and developer experience are preferred for a project. MercadoPago could be added as a secondary provider in a future phase.

**Custom payment processing:** Not viable; PCI-DSS compliance for storing card data is prohibitively expensive and risky for a small team.

## Links

- Related: ADR-014 (Celery), ADR-015 (outbox), ADR-021 (webhooks), ADR-024 (idempotency)