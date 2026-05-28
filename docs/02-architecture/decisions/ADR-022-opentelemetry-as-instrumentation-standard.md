# ADR-022: OpenTelemetry as Instrumentation Standard

- Status: Accepted
- Date: 05-20-2026
- Tags: observability, monitoring, operations

## Context

Operating a distributed system (API + workers + DB + Redis + RabbitMQ) in production requires visibility into request latency, error rates, and the path a request takes through the system. Without structured observability, diagnosing production incidents depends on intuition rather than data.

Three observability signals are required:
- **Logs** — structured, correlated to requests.
- **Metrics** — aggregated measurements (latency histograms, error counters).
- **Traces** — end-to-end request journeys across services and queues.

## Decision

OpenTelemetry (OTel) will be the instrumentation standard for all three signals. No vendor-specific SDK will be embedded in application code.

Implementation:
- **Traces:** `opentelemetry-sdk` with `opentelemetry-instrumentation-fastapi`, `opentelemetry-instrumentation-sqlalchemy`, and `opentelemetry-instrumentation-celery` for automatic span creation. Traces are exported to an OTel Collector (sidecar or dedicated deployment) which forwards to the configured backend (Grafana Tempo or Jaeger).
- **Metrics:** OTel metrics SDK with a Prometheus exporter. Prometheus scrapes the `/metrics` endpoint on each pod. Grafana dashboards visualize p95/p99 latency histograms, 5xx error rates, queue depth, and business metrics (certificates issued, active enrollments, emails sent).
- **Logs:** Structured JSON logs via `structlog`, enriched with `trace_id`, `span_id`, and `request_id` on every log line for correlation across signals. Logs are shipped to CloudWatch (production on AWS) or Loki (self-hosted alternative).
- A `request_id` (UUID v4) is injected by ASGI middleware on every incoming request and propagated through the call stack via Python context variables. It is returned in the `X-Request-ID` response header and included in all log lines and OTel span attributes.
- Celery tasks inherit the trace context from the enqueuing request via OTel context propagation headers embedded in the task headers, enabling end-to-end traces from HTTP request through to background job completion.
- An **Observability Guide** (`docs/04-operations/observability-guide.md`) documents how to investigate an incident using all three signals, what each dashboard panel means, and how to follow a trace from the API through the database and into a worker.

## Consequences

**Positive:**
- Vendor-neutral instrumentation: switching from Jaeger to Tempo or from Prometheus to a managed OTLP endpoint requires only collector configuration changes, not application code changes.
- Automatic instrumentation for FastAPI, SQLAlchemy, and Celery covers the majority of I/O spans without manual code.
- Correlated logs + traces + metrics significantly reduce mean time to diagnosis (MTTD) during incidents.
- OTel is the CNCF standard; familiarity with it is directly transferable to other enterprise environments.

**Negative:**
- OTel SDK adds some overhead (span creation, context propagation). This is negligible for I/O-bound workloads but should be measured during load tests.
- The collector is an additional component to operate and configure.
- Cardinality management in Prometheus requires discipline; high-cardinality labels (e.g., per-user metrics) can cause memory issues.

**Neutral:**
- SLO/SLI alerting (v4) is built on top of the Prometheus metrics established here; the metric naming conventions adopted now define the alerting surface later.

## Alternatives Considered

**Datadog / New Relic agent:** Proprietary agents with vendor lock-in. OTel's vendor-neutral model is preferred for a portfolio project and for production cost control.

**Custom logging only:** Logs without traces and metrics are insufficient for diagnosing latency issues or understanding request flows through background workers. Rejected.

**Sentry for error tracking:** Sentry is a complementary tool (error aggregation and alerting) and may be added alongside OTel, but it does not replace structured tracing and metrics.

## Links

- Related: ADR-014 (Celery), ADR-008 (PostgreSQL/SQLAlchemy tracing), ADR-027 (Helm/Kubernetes deployment of collector)
- Reference: opentelemetry.io, CNCF Observability Whitepaper