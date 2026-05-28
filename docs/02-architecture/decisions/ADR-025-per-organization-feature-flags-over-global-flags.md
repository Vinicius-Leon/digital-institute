# ADR-025: Per-Organization Feature Flags over Global Flags

- Status: Accepted
- Date: 05-23-2026
- Tags: product, multi-tenancy, operations

## Context

As the platform evolves, new features need to be introduced incrementally: rolled out to a subset of organizations for testing before general availability, enabled only for organizations on specific plans, or disabled per organization in response to an issue. A global feature flag system (on/off for all tenants) does not provide the granularity needed in a multi-tenant SaaS context.

## Decision

Feature flags will be scoped per organization. A flag that is enabled for Org A has no effect on Org B.

Implementation:
- A `feature_flags` table stores `(organization_id, flag_name, enabled, metadata JSONB)`. The `metadata` field allows storing flag-specific configuration (e.g., a rollout percentage or an expiry date).
- Flag state is cached in Redis with a short TTL (e.g., 60 seconds) to avoid a database read on every request. Cache is invalidated on flag update.
- The application resolves the organization context from the JWT (see ADR-006) and checks flag state in a `FeatureFlagService` injected via FastAPI's dependency system.
- `admin_org` users can manage their organization's flags via an admin endpoint. A super-admin role (platform operator) can manage flags across all organizations.
- Flag names are defined as Python string constants (or an Enum) in the codebase to prevent typo-based bugs.

Example flags: `payments_enabled`, `oidc_sso_enabled`, `rag_assistant_enabled`, `advanced_reporting_enabled`.

## Consequences

**Positive:**
- Precise control: a new feature can be enabled for a single organization (e.g., a pilot customer) before wider rollout.
- Aligns with the multi-tenant model (ADR-002) where organizations are the unit of isolation.
- Flag checks are fast (Redis cache hit) and do not add measurable latency.
- Decouples deployment from feature release: code ships dark, features activate via flag without a deploy.

**Negative:**
- Flag proliferation over time creates maintenance burden; a process for retiring flags after full rollout must be established.
- Redis cache TTL means flag changes propagate with up to TTL delay; for security-sensitive flags (e.g., disabling an org's access), immediate propagation may be required (cache invalidation on write).

**Neutral:**
- This is not a full feature management platform (LaunchDarkly, Unleash); it is a lightweight, domain-integrated implementation appropriate for the current scale.

## Alternatives Considered

**Global feature flags:** Cannot serve different feature sets to different organizations. Rejected for a multi-tenant product.

**LaunchDarkly / Unleash:** Purpose-built feature flag platforms with advanced targeting, analytics, and SDKs. Valid at larger scale but introduce a vendor dependency and cost at this stage. May be adopted in a future phase if the custom implementation becomes insufficient.

**Plan-based feature gating (code-level `if org.plan == "pro"`):** Hard-coded plan checks are brittle and require code changes to modify gating logic. Feature flags allow runtime control without deployment. Rejected as the sole mechanism.

## Links

- Related: ADR-002 (multi-tenancy), ADR-006 (JWT/org context), ADR-013 (Redis cache)