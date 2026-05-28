# ADR-001: Modular Monolith over Microservices

- Status: Accepted
- Date: 04-29-2026
- Tags: architecture, foundation

## Context

The Digital Institute platform needs to support multiple functional domains — courses, enrollments, attendance, certificates, payments, notifications, and content — from day one. The product is in its early
stages, meaning requirements will evolve and refactoring cost must remain low.

Microservices offer strong isolation and independent deployability but require significant operational overhead: service discovery inter-service communication, distributed tracing, independent CI pipelines, and eventual consistency management. At this stage, that overhead would slow down development and make the codebase harder to reason about without providing meaningful benefits.

A big-ball-of-mud monolith, on the other hand, tends to accumulate implicit coupling over time, making future extraction painful.

## Decision

I will build the system as a modular monolith: a single deployable unit organized into well-defined internal modules (e.g., `courses`, `enrollments`, `certificates`, `payments`, `notifications`), each with its own controller/service/repository layers, domain models, and clearly defined interfaces for cross-module communication.

Modules communicate through explicit service calls or internal events, never by accessing each other's repositories directly. This enforces boundaries without the network overhead and operational complexity of microservices.

## Consequences

**Positive:**
- Single deployment unit simplifies CI/CD, local development, and operational runbooks.
- Explicit module boundaries keep the codebase navigable and make future extraction to services possible if the need arises.
- Shared database transactions are straightforward, avoiding distributed transaction complexity.
- Easier end-to-end testing and debugging.

**Negative:**
- All modules share the same runtime; a CPU-intensive module can affect others.
- Scaling is coarse-grained: the entire application scales together, not individual modules.
- Discipline is required to prevent boundary violations over time; without enforcement, it can degrade into a monolith without the "modular" part.

**Neutral:**
- A future extraction of a module into a standalone service remains viable if a specific module's load demands it, precisely because boundaries are explicit from the start.

## Alternatives Considered

**Microservices from day one:** Rejected due to operational overhead
disproportionate to team size. Distributed tracing, service mesh, independent deployments, and inter-service contracts would consume more time than building the actual product.

**Unstructured monolith:** Rejected because the absence of enforced module boundaries leads to implicit coupling that makes the codebase increasingly difficult to maintain and test.

## Links

- Related: ADR-002 (row-level multi-tenancy), ADR-004 (FastAPI)
- Reference: "Modular Monolith with DDD" — Kamil Grzybek