# ADR-026: GitHub Actions for CI/CD

- Status: Accepted
- Date: 05-24-2026
- Tags: ci-cd, operations, delivery

## Context

The project requires automated pipelines for linting, type checking, testing, container image building, and deployment. The pipeline must integrate with the version control host, support environment-specific deployments, and be maintainable by a small team without dedicated DevOps infrastructure.

## Decision

GitHub Actions will be the CI/CD platform. All pipeline configuration lives in `.github/workflows/` as YAML files, versioned alongside the application code.

Pipeline structure:

**CI pipeline** (triggered on every PR and push to `main`):
1. `lint-and-format` — `ruff check` + `black --check`
2. `type-check` — `mypy` in strict mode
3. `unit-tests` — `pytest tests/unit/` with coverage threshold enforcement
4. `integration-tests` — `pytest tests/integration/` with services (Postgres, Redis, RabbitMQ) spun up via `docker compose` inside the runner
5. `build` — Docker image build (no push on PRs)

**CD pipeline** (triggered on push to `main` after CI passes, or on tagged release):
1. Build and push Docker image to Amazon ECR, tagged with the commit SHA and `latest`.
2. Deploy to the target environment:
   - **v1–v3 (EC2/ECS):** SSH deploy or ECS task definition update via `aws ecs update-service`.
   - **v4+ (Kubernetes/Helm):** `helm upgrade --install` against the target cluster using kubeconfig stored as a GitHub Actions secret.
3. Run smoke tests against the deployed environment.

**Security pipeline** (triggered on schedule and on push to `main`):
- `pip-audit` for dependency vulnerability scanning (SCA).
- `trufflehog` or `gitleaks` for secret scanning.
- SBOM generation (v4, `syft`).

Secrets (AWS credentials, kubeconfig, signing keys) are stored in GitHub Actions Secrets and accessed via `${{ secrets.* }}` — never hardcoded in workflow files.

## Consequences

**Positive:**
- Zero additional infrastructure: GitHub Actions runners are managed by GitHub.
- Workflow files are in the same repository as the code; PRs to change the pipeline go through the same review process as application changes.
- Native integration with GitHub PRs: status checks block merges on CI failure.
- Matrix builds and reusable workflows reduce duplication across multiple pipeline variants.

**Negative:**
- GitHub Actions has a free tier limit on private repositories; at higher usage, costs apply. Acceptable for a portfolio project.
- Pipeline YAML can become complex and verbose for multi-environment deployments; reusable workflows and composite actions mitigate this.
- Vendor lock-in to GitHub; migrating to GitLab CI or CircleCI would require rewriting workflows (though the underlying scripts remain portable).

**Neutral:**
- The CI pipeline enforces the quality gates described in the contributionguidelines (`CONTRIBUTING.md`): a PR cannot be merged with failing lint, type checks, or tests.

## Alternatives Considered

**Jenkins:** Powerful but requires self-hosted infrastructure, plugin management, and significant operational overhead. Rejected.

**CircleCI / GitLab CI:** Viable alternatives, but GitHub Actions is the natural choice given the repository is hosted on GitHub. Migration is possible if requirements change.

**ArgoCD (for CD only):** A complementary GitOps tool for Kubernetes deployments. May be introduced alongside GitHub Actions in v4 for declarative cluster state management.

## Links

- Related: ADR-027 (Helm), ADR-028 (Terraform)