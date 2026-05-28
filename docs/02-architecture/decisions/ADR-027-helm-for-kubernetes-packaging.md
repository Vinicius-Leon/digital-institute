# ADR-027: Helm for Kubernetes Packaging

- Status: Accepted
- Date: 05-25-2026
- Tags: kubernetes, infrastructure, deployment

## Context

The v4 phase deploys the application to Kubernetes. A Kubernetes deployment consists of multiple resource types: Deployments, Services, Ingress, ConfigMaps, Secrets, HorizontalPodAutoscaler, PodDisruptionBudget, and init containers for migrations. Managing these as raw YAML manifests across multiple environments (staging, production) leads to configuration drift and error-prone copy-paste.

A packaging and templating tool is needed to manage environment-specific values cleanly and deploy atomically.

## Decision

Helm will be used to package and deploy all Kubernetes resources for the platform.

Chart structure:

    helm/
      instituto-digital/
        Chart.yaml
        values.yaml
        values-staging.yaml
        values-production.yaml
        templates/
          api-deployment.yaml
          worker-deployment.yaml
          api-service.yaml
          ingress.yaml
          configmap.yaml
          migration-job.yaml
          hpa.yaml
          pdb.yaml
          serviceaccount.yaml

Key decisions within the chart:

- **Alembic migrations** run as a Kubernetes `Job` (or init container on the API Deployment) before new API pods receive traffic, ensuring the schema is current before the application starts.
- **Secrets** are not stored in the chart. They are injected from AWS Secrets Manager or SSM Parameter Store via the External Secrets Operator, or mounted as environment variables from Kubernetes Secrets created out-of-band.
- **Readiness and liveness probes** target the `/health` endpoint on the API, which checks DB, Redis, and RabbitMQ connectivity.
- **Resource requests and limits** are defined for every container. Defaults live in `values.yaml` and are overridden per environment.
- The chart is deployed via `helm upgrade --install` in the GitHub Actions CD pipeline (ADR-026), with `--atomic` to roll back automatically on failure.

## Consequences

**Positive:**
- A single `helm upgrade` command deploys the entire application stack with environment-specific values.
- The `--atomic` flag provides automatic rollback if any resource fails to become ready within the timeout.
- Helm chart versioning (`Chart.yaml`) aligns with application releases.
- Templating eliminates environment-specific YAML duplication.

**Negative:**
- Helm's templating language (Go templates) is verbose and can be confusing for complex conditional logic.
- Helm manages release state in-cluster via Secrets; loss of that state requires `helm uninstall` followed by reinstall.
- Debugging a failed release requires working across `helm status`, `helm history`, and `kubectl` simultaneously.

**Neutral:**
- Kustomize is a valid alternative used by some teams. Helm is chosen here for its package registry support and wider adoption in enterprise environments.

## Alternatives Considered

**Raw kubectl manifests:** No templating, no release management, high environment drift risk. Rejected for multi-environment deployments.

**Kustomize:** Overlay-based, no templating engine. Simpler than Helm for some use cases but less ergonomic for multi-environment value management. May be used as a complement in a future phase.

**Pulumi / CDK for Kubernetes:** Infrastructure as code in a general-purpose language. More powerful than Helm but adds a separate runtime dependency. Terraform covers the AWS layer (ADR-028); Helm is sufficient for Kubernetes packaging.

## Links

- Related: ADR-026 (GitHub Actions/CD), ADR-028 (Terraform), ADR-022 (OpenTelemetry/observability)