# ADR-007: Argon2 for Password Hashing

- Status: Accepted
- Date: 05-05-2026
- Tags: security, auth

## Context

User passwords must be stored as hashes in the database. The hashing algorithm must be resistant to brute-force and GPU-accelerated attacks. The choice of algorithm has direct security implications in the event of a database breach.

OWASP explicitly recommends Argon2id as the first choice for password hashing as of their current Password Storage Cheat Sheet.

## Decision

We will use Argon2id via the `argon2-cffi` Python library for all password hashing and verification operations.

Default parameters (aligned with OWASP minimums):
- `time_cost`: 2 iterations
- `memory_cost`: 65536 KB (64 MB)
- `parallelism`: 2

These parameters will be reviewed and increased as server capacity allows.
The `PasswordHasher` instance will be a singleton initialized at application startup to avoid repeated configuration parsing.

Passwords will never be logged, included in error messages, or returned in any API response. The plain-text password is discarded immediately after hashing.

## Consequences

**Positive:**
- Argon2id is the current OWASP-recommended algorithm, resistant to GPU and ASIC attacks due to its memory-hard design.
- The `argon2-cffi` library wraps the reference C implementation; it is well-maintained and widely audited.
- Automatic rehashing on parameter upgrades is straightforward: check hash validity on login and rehash if parameters differ.

**Negative:**
- Memory and CPU cost per hash operation is intentionally high; under heavy concurrent login load, this can become a bottleneck. Mitigated by rate limiting on authentication endpoints.

**Neutral:**
- bcrypt and scrypt remain acceptable fallbacks per OWASP but are not selected here because Argon2id strictly dominates them in the current threat model.

## Alternatives Considered

**bcrypt:** OWASP's second recommendation. Battle-tested, but limited to 72 bytes of input and does not offer memory-hardness comparable to Argon2.

**scrypt:** Memory-hard like Argon2 but less flexible and harder to tune. Argon2id is preferred by OWASP and the broader cryptography community.

**PBKDF2:** Required for FIPS compliance contexts, but inferior to Argon2 in resistance to GPU attacks. Not applicable here.

## Links

- Related: ADR-006 (JWT auth), ADR-016 (RBAC)
- Reference: OWASP Password Storage Cheat Sheet