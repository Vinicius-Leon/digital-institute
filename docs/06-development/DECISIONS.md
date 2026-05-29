# Decisions, Errors & Learnings
## Prototype — Technical Foundation

> This document records every meaningful decision, failure, and learning
> from building this project from scratch. Written honestly — not to show
> a perfect process, but a real one.

---

## Architecture Decisions

### Why `src/` layout instead of a flat structure
Putting all source code inside `src/institute/` instead of directly in
the root forces a clean separation between the package and project
tooling (tests, config files, scripts). It also prevents a subtle bug
where Python imports the local folder instead of the installed package,
which would hide import errors that only appear in production.

### Why Argon2 instead of bcrypt
Argon2 won the Password Hashing Competition in 2015 and is resistant to
GPU-based attacks by design. bcrypt is still safe but dates from 1999.
In 2024+, Argon2 is the correct default for new projects.

### Why inject PasswordHasher as a dependency
The first implementation used a module-level `ph = PasswordHasher()`
instance called directly inside the service. This made unit testing
impossible — `PasswordHasher` is a C extension and its methods are
read-only, so `unittest.mock.patch` raised `AttributeError: read-only`.

The fix was to inject the hasher through the constructor with a default:

```python
def __init__(self, db: AsyncSession, password_hasher=None):
    self._ph = password_hasher or PasswordHasher()
```

Tests pass a `MagicMock()`. Production uses the real hasher.
This is the Dependency Inversion Principle in practice — not just theory.

### Why rollback instead of DELETE in test fixtures
The `conftest.py` wraps each test in a transaction that is rolled back
at the end instead of deleting rows after each test. Rollback is
significantly faster and guarantees a clean state even if a test crashes
mid-execution without reaching the cleanup code.

### Why a separate `institute_test` database
Running tests against the development database risks corrupting data
you are actively using. A separate database gives full isolation at zero
cost since both run in the same Postgres container.

### Why `get_current_user` as a FastAPI dependency
Authentication logic lives in `dependencies.py` and is injected via
`Depends()`. This means any future endpoint can require authentication
with a single line. It also makes the dependency overridable in tests —
FastAPI's `dependency_overrides` lets tests inject a fake user without
touching the JWT logic at all.

---

## What Broke and Why

### `ModuleNotFoundError: No module named 'institute'`
**When:** First time running Alembic or pytest after cloning.  
**Why:** The `src/` layout requires the package to be installed in the
virtualenv. Without `pip install -e .`, Python has no idea that
`src/institute/` is a package — it just sees a folder.  
**Fix:** Always run `pip install -e .` after cloning or after changing
`pyproject.toml`.  
**Rule learned:** `src/` layout is safer but requires this extra step.
Add it to the README as step 1.

### `Connection refused` when running Alembic
**When:** Running `alembic upgrade head` immediately after
`docker compose up`.  
**Why:** Postgres takes a few seconds to initialize. The container
starts before the database is actually ready to accept connections.  
**Fix:** Wait for the healthcheck to pass. `docker compose ps` shows
`healthy` when Postgres is ready.  
**Rule learned:** Container running ≠ service ready. Always check
healthchecks, especially in CI pipelines.

### `FATAL: password authentication failed`
**When:** After changing credentials in `.env` or `docker-compose.yml`.  
**Why:** Docker volumes persist data from previous runs. The Postgres
container initializes credentials only on first start. Changing `.env`
after the volume exists has no effect — the old credentials are baked
into the volume.  
**Fix:** `docker compose down -v` destroys the volume and forces
reinitialization with the new credentials.  
**Warning:** In production, `down -v` deletes all data permanently.
Never run it on a production volume.

### `failed to resolve host 'postgres'`
**When:** Running Alembic or tests from the local terminal.  
**Why:** `postgres` is the Docker service name — it only resolves inside
the Docker network. Outside Docker (local terminal, Alembic, pytest),
the correct hostname is `localhost`.  
**Fix:** Use `localhost` in `.env` for local development. The
`docker-compose.yml` service name is only for container-to-container
communication.  
**Rule learned:** Two network contexts always exist — inside Docker and
outside Docker. `DATABASE_URL` means different things in each.

### `AttributeError: 'PasswordHasher' object attribute 'verify' is read-only`
**When:** Running unit tests that tried to patch `ph.verify`.  
**Why:** `PasswordHasher` is implemented as a C extension (libargon2).
C extension attributes are read-only slots — `unittest.mock.patch`
cannot replace them at runtime.  
**First attempt:** Patch `PasswordHasher.verify` on the class instead
of the instance. Still failed for the same reason.  
**Actual fix:** Inject `PasswordHasher` as a constructor dependency and
pass a `MagicMock()` in tests. Never patch C extensions — redesign
around them.  
**Rule learned:** When something is untestable, the problem is usually
the design, not the test.

### `argon2.exceptions.VerificationError: Decoding failed`
**When:** Unit test for login with nonexistent user.  
**Why:** The timing-attack protection code used a fake hash string that
was not a valid Argon2 hash. `ph.verify()` raised `VerificationError`
(decoding failure) instead of `VerifyMismatchError` (wrong password).
The `except` clause only caught `VerifyMismatchError`, so the exception
propagated up instead of being silently swallowed.  
**Fix:** Catch both `VerifyMismatchError` and `VerificationError` in the
dummy verification block.  
**Rule learned:** Timing-attack protection dummy hashes must be valid
hashes, or the error handling must account for malformed input.

### `TypeError: 'NoneType' object is not subscriptable` in Celery task test
**When:** Testing `send_notification` with `task.delay()` and eager mode.  
**Why:** `task_always_eager=True` makes Celery execute tasks
synchronously, but `result.result` is only populated when a result
backend is configured. Without a backend, it returns `None`.  
**First attempt:** Use `result.get()` instead of `result.result`.
Still hung indefinitely — `delay()` was still trying to contact the
broker even in eager mode.  
**Actual fix:** Call the task function directly without `.delay()`.
Unit tests test logic, not the Celery infrastructure.

```python
# wrong for unit tests
result = send_notification.delay(user_id="123", event="test", payload={})

# correct for unit tests  
result = send_notification(user_id="123", event="test", payload={})
```

**Rule learned:** `.delay()` tests the broker. Calling directly tests
the function. Unit tests should do the latter.

### Worker container failing with `secret_key field required`
**When:** `docker compose logs worker` after bringing up the stack.  
**Why:** The worker container did not have the `SECRET_KEY` environment
variable set. The `Settings` Pydantic model requires it and raises a
`ValidationError` when it is missing, which prevents the Celery app
from loading entirely.  
**Fix:** Add `SECRET_KEY` to the worker service environment in
`docker-compose.yml` or pass it via `.env` file mounted into the
container.  
**Rule learned:** Every service that imports application code inherits
all configuration requirements. Worker, beat scheduler, and API all
need the full `.env`.

### `ruff`, `black`, `mypy`, `pytest` not found outside virtualenv
**When:** Running linting commands without activating the virtualenv.  
**Why:** These tools are installed inside `.venv/`, not system-wide.
The shell does not know about them until the virtualenv is activated.  
**Fix:** `source .venv/bin/activate` before running any project tooling.  
**Rule learned:** Always check `which pytest` if a command is not found.
If it points outside `.venv/`, the virtualenv is not active.

---

## Test Coverage Journey

| Stage | Coverage | Notes |
|---|---|---|
| Initial (3 tests) | — | No coverage configured |
| After auth unit tests | 75% | Below 80% threshold |
| After adding login tests | 76% | Still failing |
| After injecting hasher | 77% | Tests passing, coverage still low |
| After health + tasks + integration | **90%** | All 25 tests green |

The jump from 77% to 90% came from covering four files that were at 0%:
`dependencies.py`, `tasks.py`, `worker.py`, and `database.py`. The
lesson is that high coverage requires testing infrastructure code too —
not just business logic.

---

## What the Linter Caught

### `B904` — raise without `from` inside except clause
Ruff flagged this pattern:

```python
except VerifyMismatchError:
    raise UnauthorizedError("Invalid email or password.")
```

The correct version makes the intent explicit:

```python
except VerifyMismatchError:
    raise UnauthorizedError("Invalid email or password.") from None
```

`from None` suppresses the exception chain intentionally — callers
should not see `VerifyMismatchError` leaking through `UnauthorizedError`.
`from err` would preserve the chain for debugging. Choosing between them
is a deliberate decision, not an accident.

---

## Patterns That Proved Useful

**Dependency injection for testability.** Any class that is hard to test
probably has a hidden dependency. Make it explicit in the constructor.

**Two-context mental model for networking.** Always ask: is this
hostname resolving inside or outside Docker? Keep both contexts in mind
when writing `DATABASE_URL` and `BROKER_URL`.

**Test the path, not the mock.** Several tests were written to patch
something that turned out to be unpatchable. The better question is
always: what code path am I trying to exercise, and how do I exercise
it without real infrastructure?

**Commit at logical boundaries.** Four commits for this phase — fixtures,
production fixes, unit tests, integration tests. Each commit tells a
coherent story and can be reverted independently if needed.

---

## Commands That Saved Time

```bash
# See exactly which lines are not covered
pytest --cov=src --cov-report=term-missing

# Open coverage report in WSL
wslpath -w htmlcov/index.html

# Amend last commit before push
git add <forgotten-file>
git commit --amend --no-edit

# Verify what files are in the last commit
git show --stat HEAD

# Force Postgres reinitialization with new credentials
docker compose down -v && docker compose up -d
```