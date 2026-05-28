# ADR-016: RBAC with Predefined Roles over ABAC

- Status: Accepted
- Date: 05-14-2026
- Tags: auth, security, authorization

## Context

The platform serves users with distinct operational responsibilities: organization administrators, instructors, students, and blog editors. Each role has a well-understood, stable set of permitted actions. Authorization decisions must be enforceable at the API layer and auditable.

Attribute-Based Access Control (ABAC) allows fine-grained, policy-driven authorization based on arbitrary attributes of the user, resource, and environment. It is more flexible but significantly more complex to implement, test, and reason about.

## Decision

I will implement Role-Based Access Control (RBAC) with a fixed set of predefined roles:

| Role | Scope | Description |
|------|-------|-------------|
| `admin_org` | Per organization | Full control within the organization |
| `instructor` | Per organization | Manage their own courses, classes, attendance |
| `student` | Per organization | Enroll, attend, view own certificates |
| `blog_editor` | Per organization | Create and publish blog content |

Authorization rules:
- Role is embedded in the JWT payload (see ADR-006) and verified in FastAPI dependencies.
- All authorization checks are performed in the service layer, not the controller, to keep enforcement close to business logic.
- Role assignments are scoped to an organization; a user can have different roles in different organizations.
- A permission matrix document (`docs/01-product/rbac-matrix.md`) defines allowed actions per role per module and is kept up to date as a reference.

## Consequences

**Positive:**
- Simple to implement, test, and explain to stakeholders.
- Roles are stable enough that they can be embedded in the JWT without frequent invalidation.
- The permission matrix is human-readable and auditable.
- RBAC is well-understood by security auditors and enterprise customers.

**Negative:**
- New permission requirements that don't fit cleanly into the predefined roles require schema changes or new roles.
- RBAC cannot express contextual rules like "an instructor can only modify their own classes" without supplementing with object ownership checks in the service layer.

**Neutral:**
- Object ownership checks (e.g., instructor can only edit their own course) are implemented as service-layer conditions alongside role checks, not as a full ABAC policy engine.

## Alternatives Considered

**ABAC with a policy engine (e.g., OPA/Cedar):** Maximum flexibility but requires a policy language, a policy store, and runtime policy evaluation. Complexity not justified for the current role set.

**Permission-based system (granular permissions rather than roles):** More flexible than named roles but adds complexity to token payload and permission management. May be introduced in a future phase if the role set becomes insufficient.

## Links

- Related: ADR-002 (multi-tenancy), ADR-006 (JWT), ADR-017 (OIDC)