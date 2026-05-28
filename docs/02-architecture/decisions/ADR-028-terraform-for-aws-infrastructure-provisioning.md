# ADR-028: Terraform for AWS Infrastructure Provisioning

- Status: Accepted
- Date: 05-26-2026
- Tags: infrastructure, aws, iac

## Context

The platform runs on AWS and requires reproducible provisioning of cloud resources: VPC, subnets, RDS, ElastiCache, S3 buckets, IAM roles and policies, ECR repositories, and (in v4) an EKS cluster. Manual provisioning via the AWS Console is not repeatable, not version-controlled, and not reviewable.

Infrastructure as Code (IaC) is required from the beginning to ensure environments are consistent and provisionable from scratch.

## Decision

Terraform will be used for all AWS infrastructure provisioning.

Repository structure:

    terraform/
      modules/
        networking/      # VPC, subnets, security groups, NAT gateway
        database/        # RDS PostgreSQL, parameter groups, subnet group
        cache/           # ElastiCache Redis
        storage/         # S3 buckets, bucket policies, lifecycle rules
        iam/             # IAM roles, policies, instance profiles
        ecr/             # ECR repositories
        eks/             # EKS cluster (v4)
      environments/
        staging/
          main.tf
          variables.tf
          terraform.tfvars
          backend.tf
        production/
          main.tf
          variables.tf
          backend.tf

State management:

- Remote state is stored in an S3 bucket with versioning enabled.
- A DynamoDB table handles state locking to prevent concurrent applies.
- The S3 bucket and DynamoDB table are the only resources bootstrapped manually (or via a separate `terraform/bootstrap/` root). All other resources are managed by Terraform.

Sensitive values (database passwords, secret keys) are never stored in `.tfvars` or committed to the repository. They are passed via environment variables (`TF_VAR_*`) or pulled from AWS Secrets Manager via a Terraform data source.

Terraform applies run in the GitHub Actions CD pipeline (ADR-026) using an IAM role with least-privilege permissions, authenticated via OIDC — no long-lived access keys are stored in CI secrets.

## Consequences

**Positive:**
- Infrastructure changes go through the same PR review process as application code. `terraform plan` output is posted as a PR comment; apply runs only after merge.
- Reproducible environments: staging and production are provisioned from the same modules with different variable values.
- State in S3 with DynamoDB locking prevents race conditions in concurrent CI runs.
- Modules organized by responsibility (`networking`, `database`, `storage`) keep the codebase navigable and allow independent changes to each layer.

**Negative:**
- Terraform state can drift from actual AWS state if resources are modified outside Terraform. A `terraform plan` check in CI catches most drift.
- The EKS module is complex; managed node groups, OIDC provider configuration, and add-on ordering require careful attention.
- `terraform destroy` destroys infrastructure in a single command. State lock and CI controls are the primary safeguards against accidental destruction.

**Neutral:**
- A `terraform/README.md` documents how to bootstrap the backend, how to run plan and apply locally with appropriate AWS credentials, and how CI applies changes automatically.

## Alternatives Considered

**AWS CloudFormation:** Native to AWS but more verbose, YAML/JSON-only, and lacks Terraform's ecosystem of community modules and providers. Rejected.

**Pulumi:** Infrastructure as code in Python, which matches the primary language. A valid alternative; Terraform is chosen for its wider enterprise adoption and the specific career value of Terraform familiarity.

**AWS CDK:** Similar reasoning to Pulumi. Terraform wins on ecosystem maturity and enterprise prevalence.

## Links

- Related: ADR-026 (GitHub Actions), ADR-027 (Helm/Kubernetes)
- Reference: developer.hashicorp.com/terraform