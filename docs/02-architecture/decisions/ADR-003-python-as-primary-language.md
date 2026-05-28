# ADR-003: Python as Primary Language

- Status: Accepted
- Date: 05-01-2026
- Tags: foundation, language

## Context

The project requires a backend language for API development, background job processing, ETL pipelines, and LLM integration. The choice of language has long-term consequences for hiring, tooling, library availability, and development velocity.

Key requirements:
- Strong ecosystem for web frameworks, ORMs, task queues, and data tooling.
- First-class support in the chosen frameworks (FastAPI, Celery, Airflow, SQLAlchemy).
- Sufficient typing support for a maintainable, testable codebase.
- Familiarity with the language.

## Decision

Python (3.12+) will be the primary and only backend language. All application code — API handlers, services, repositories, background workers, ETL pipelines, and scripts — will be written in Python.

I will use:
- Type annotations throughout, enforced by `mypy` in strict mode.
- `pip-tools` (`pip-compile` + `pip-sync`) for deterministic dependency management.
- `ruff` and `black` for linting and formatting.

## Consequences

**Positive:**
- FastAPI, SQLAlchemy, Celery, Alembic, Airflow, and pgvector all have native Python support.
- The data science and LLM ecosystem (LangChain, OpenAI SDK, sentence- transformers) is Python-first.
- Large talent pool and extensive community resources.
- Type annotations with mypy catch entire categories of bugs at static analysis time.

**Negative:**
- Python's GIL limits true CPU-bound parallelism within a single process; CPU-intensive tasks must be offloaded to Celery workers.
- Raw performance is lower than compiled languages (Go, Rust); this is mitigated by async I/O, connection pooling, and caching.

**Neutral:**
- JavaScript/TypeScript is used minimally in the front end (fetch calls only), as documented in the front-end scope.

## Alternatives Considered

**Go:** Excellent performance and concurrency, but the data/ML ecosystem is immature compared to Python, and FastAPI + SQLAlchemy equivalents do not exist.

**Node.js/TypeScript:** Strong ecosystem for APIs, but the data tooling (ORMs, Airflow, pgvector clients, LLM SDKs) is significantly weaker than Python's.

## Links

- Related: ADR-004 (FastAPI), ADR-005 (Pydantic), ADR-009 (SQLAlchemy)