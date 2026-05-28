# ADR-029: Airflow over Custom Scripts for ETL Orchestration

- Status: Accepted
- Date: 05-27-2026
- Tags: etl, data, orchestration

## Context

The v6 phase introduces operational ETL pipelines: exporting participation data (enrollment funnel, completion rates, trends by organization), feeding the RAG pipeline (extracting and embedding course materials), and potentially syncing data to external analytics tools.

ETL pipelines have specific requirements that differ from regular background jobs: complex dependency graphs between tasks, retry logic at the task level, execution history and audit trail, scheduled and ad-hoc triggering, and visibility into pipeline health without reading code.

Custom scripts managed by cron lack all of these properties at scale.

## Decision

Apache Airflow will be used for ETL pipeline orchestration in v6.

Implementation approach:
- Airflow runs as a separate service (Airflow Scheduler + Webserver + Workers) deployed alongside the main application, either via Docker Compose (local) or a dedicated Kubernetes Deployment (production).
- DAGs (Directed Acyclic Graphs) are defined in Python in a `dags/` directory versioned in the same repository.
- Airflow connects to the platform's PostgreSQL database (read-only replica or direct connection with read-only credentials) to extract data; it never writes to the application database directly.
- Primary pipelines:
  - **Impact report pipeline:** nightly aggregation of enrollment, attendance, completion, and certificate data per organization, written to a reporting schema or an S3 data lake prefix.
  - **Embedding pipeline:** extracts new/updated course materials, generates embeddings via the LLM provider API, and upserts into `pgvector` (see ADR-012).
- Airflow's built-in retry, SLA monitoring, and email alerting on DAG failure are configured from the start.
- The Airflow metadata database uses a separate PostgreSQL database (not shared with the application) to avoid coupling.

## Consequences

**Positive:**
- Airflow's DAG model handles complex task dependencies, fan-out, and conditional branching that cron scripts cannot express cleanly.
- The Airflow UI provides execution history, task logs, and re-run capability without SSH access to the server.
- Airflow is a standard tool in data engineering; familiarity is directly transferable to data platform roles.
- Python DAGs allow reuse of existing application utilities (data models, service interfaces via direct import or API calls).

**Negative:**
- Airflow is operationally heavy: scheduler, webserver, and workers are separate processes with their own resource requirements.
- The learning curve for DAG authoring, connection management, and Airflow configuration is significant.
- Airflow is designed for batch workloads; it is not a replacement for Celery for real-time or latency-sensitive background jobs (ADR-014).

**Neutral:**
- Prefect is explicitly acknowledged as an alternative with a simpler operational model (managed cloud tier available). Airflow is chosen for its wider enterprise adoption and the career value of Airflow experience. If Airflow's operational overhead proves excessive for the v6 scope, Prefect Cloud can be substituted with minimal DAG logic changes.

## Alternatives Considered

**Prefect:** Modern, Python-first, with a managed cloud option that eliminates the operational burden. Strong alternative; not chosen here because Airflow's enterprise prevalence makes it a stronger portfolio signal.

**Celery Beat (cron tasks only):** Suitable for simple scheduled tasks (already used for token expiry cleanup, report consolidation). Insufficient for multi-step ETL pipelines with task-level retry and dependency management. Rejected as the ETL orchestrator, though it remains in use for lightweight scheduled jobs.

**Custom Python scripts + cron:** No dependency management, no retry at the task level, no execution history, no UI. Acceptable for a single-step export but does not scale to multi-step pipelines. Rejected.

## Links

- Related: ADR-012 (pgvector/embeddings), ADR-014 (Celery, for distinguishing concerns), ADR-008 (PostgreSQL as the data source)
- Reference: airflow.apache.org