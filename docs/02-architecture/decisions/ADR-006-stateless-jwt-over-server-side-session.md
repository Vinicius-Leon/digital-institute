# ADR-006: Stateless JWT over Server-Side Sessions

- Status: Accepted
- Date: 05-04-2026
- Tags: auth, security, api

## Context

The API needs to authenticate requests from multiple clients: browser-based users (Jinja2 templates and fetch calls), and potentially external partners or integrations in the future. The authentication mechanism must work in a stateless, horizontally scalable deployment (multiple API pods behind a load balancer) without requiring sticky sessions.

Server-side sessions store session state in a backend store (Redis or DB) and issue an opaque session ID to the client. JWTs encode claims directly in a signed token that can be verified without a backend lookup on every request.

## Decision

Authentication will use short-lived JWT access tokens (15–60 minutes) combined with longer-lived refresh tokens stored in an HttpOnly cookie.

- Access tokens are signed with RS256 (asymmetric) or HS256 (symmetric, acceptable for single-service deployments) and verified in middleware on every authenticated request.
- Refresh tokens are stored in an HttpOnly, Secure, SameSite=Strict cookie to mitigate XSS theft.
- Token revocation for logout and security events is handled by maintaining a short-lived revocation list in Redis, keyed by token JTI, with TTL matching the access token expiry.
- The `organization_id` and `role` claims are embedded in the JWT payload to avoid a database lookup on every request for tenant context and authorization.

## Consequences

**Positive:**
- Stateless verification: any API pod can validate a token without a shared session store lookup on the hot path.
- Standard format: well-understood by integrators, compatible with OIDC (see ADR-017).
- Claims in the token reduce latency by avoiding a user record DB read on every request for basic auth checks.

**Negative:**
- Tokens cannot be instantly invalidated without the revocation list in Redis; the system accepts eventual revocation within the access token TTL window for cases not using the revocation list.
- JWT payload is base64-encoded (not encrypted); sensitive claims must not be included. The `organization_id` and `role` are acceptable; PII is not.
- Implementation complexity is higher than a simple session cookie; refresh token rotation must be handled correctly to prevent token theft.

**Neutral:**
- For server-rendered pages (Jinja2), the token may be stored in the HttpOnly cookie directly. For JS clients, the access token lives in memory and the refresh token in a cookie.
- CSRF protection is required for cookie-based flows and is enforced via SameSite=Strict and an explicit CSRF token for state-changing requests.

## Alternatives Considered

**Server-side sessions with Redis:** Simpler to revoke, but requires a Redis lookup on every request and introduces session affinity concerns.

**Opaque tokens with introspection:** Fully server-controlled but requires a network call (or cache) per request, adding latency.

## Links

- Related: ADR-007 (Argon2), ADR-013 (Redis), ADR-016 (RBAC), ADR-017 (OIDC)