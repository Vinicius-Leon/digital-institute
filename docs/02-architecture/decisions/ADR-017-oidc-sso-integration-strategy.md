# ADR-017: OIDC SSO Integration Strategy

- Status: Accepted
- Date: 05-15-2026
- Tags: auth, sso, enterprise, integrations

## Context

Enterprise and institutional customers expect to use their own identity providers (Google Workspace, Microsoft Entra, Okta, Keycloak) to authenticate users, rather than managing a separate set of credentials for this platform. OpenID Connect (OIDC) is the de facto standard for federated identity in SaaS products.

The integration must be generic enough to work with any OIDC-compliant provider without custom code per provider.

## Decision

I will implement a generic OIDC SSO integration using the Authorization Code Flow with PKCE. The integration will be delivered in v4.

Architecture:
- The platform acts as an OIDC Relying Party (RP).
- Provider configuration (issuer URL, client ID, client secret, scopes) is stored per organization in the database and loaded at runtime.
- The `Authlib` Python library handles the OIDC protocol implementation (discovery, token exchange, ID token validation).
- On successful OIDC authentication, the platform looks up or creates a local user record linked to the external provider identity (via `sub` claim).
- The platform's own JWT (ADR-006) is issued after OIDC authentication, maintaining a consistent auth model for the rest of the application.
- OIDC configuration per organization is managed by `admin_org` users.

## Consequences

**Positive:**
- Any OIDC-compliant provider works without code changes.
- Reduces credential management burden for enterprise organizations.
- Demonstrates enterprise integration capability in the portfolio.
- Authlib is a well-maintained, security-audited library for OAuth2/OIDC.

**Negative:**
- OIDC flow adds redirect-based authentication, which is more complex to test and debug than simple password auth.
- Provider misconfiguration (wrong redirect URI, expired client secret) creates a support burden.
- Just-In-Time (JIT) user provisioning requires decisions about default role assignment for new OIDC users.

**Neutral:**
- Local username/password authentication (ADR-006, ADR-007) coexists with OIDC; organizations choose which methods to enable.

## Alternatives Considered

**SAML 2.0:** Older standard, XML-based, common in enterprise environments but significantly more complex to implement than OIDC. OIDC covers the same use cases with a cleaner protocol.

**OAuth2 only (without OIDC):** OAuth2 alone does not provide identity; the ID token from OIDC is required for authentication. Rejected.

## Links

- Related: ADR-006 (JWT), ADR-016 (RBAC)
- Reference: OIDC Core Spec (openid.net/specs/openid-connect-core-1_0.html)