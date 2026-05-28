# ADR-023: Consumer-Driven Contract Tests with Pact

- Status: Accepted
- Date: 05-21-2026
- Tags: testing, contracts, quality, api

## Context

As the API surface grows and multiple consumers interact with it (the Jinja2/JS front end, webhook recipients, and potentially external partners), there is a risk that API changes break consumers silently. Standard integration tests verify that the provider behaves correctly in isolation, but they do not verify that the provider satisfies the specific expectations of each consumer.

Consumer-driven contract testing inverts this: each consumer defines what it expects from the provider, those expectations are recorded as a contract, and the provider verifies it can fulfill every registered contract independently of end-to-end tests.

## Decision

I will use Pact for consumer-driven contract testing on the most critical API contracts, introduced in v3.

Roles:
- **Consumer:** the Jinja2/JS front-end client (for rendered pages that use fetch calls to the API) and any documented external integration point.
- **Provider:** the FastAPI application.

Implementation:
- Consumer tests are written using `pact-python` and define the expected request/response pairs. Running the consumer test generates a Pact file (JSON contract).
- The Pact Broker (running locally via Docker Compose during development, or PactFlow for CI) stores and versions contracts.
- Provider verification runs as part of the CI pipeline: the FastAPI application is started against a test database, and the Pact framework replays each consumer interaction, asserting the provider's response matches the contract.
- Contract tests are scoped to the endpoints most likely to have breaking changes: authentication, enrollment, certificate retrieval, and webhook payload format.
- A section in `TESTING.md` explicitly documents which endpoints have contracts, who the consumer and provider are for each, and how to run the Pact Broker locally.

## Consequences

**Positive:**
- Breaking API changes are caught before deployment, even if the consumer is not tested in the same pipeline run.
- Contracts serve as living documentation of what each consumer actually uses, not what the provider thinks it exposes.
- Demonstrates a testing practice that is standard in mature engineering teams and differentiates the portfolio.

**Negative:**
- Pact adds tooling overhead: the Pact Broker (or PactFlow) must be running for CI verification, and consumer and provider teams must coordinate on contract updates.
- For a project where the consumer and provider are maintained by the same person/team, the overhead is higher relative to the benefit than in a multi-team environment. The benefit here is primarily demonstrating the skill, not solving an actual team coordination problem.
- Pact contracts can become stale if not maintained alongside API changes.

**Neutral:**
- Pact does not replace integration tests or end-to-end tests; it complements them by adding a consumer-perspective verification layer.

## Alternatives Considered

**OpenAPI schema validation only:** Verifies that responses conform to the schema, but does not verify that the provider satisfies the specific interactions a consumer depends on. Less precise. Retained as a complementary check, not a replacement.

**End-to-end tests for every consumer interaction:** Expensive to maintain, slow to run, and brittle. Rejected as the primary contract verification mechanism.

## Links

- Related: ADR-004 (FastAPI), ADR-005 (Pydantic/schemas)
- Reference: docs.pact.io