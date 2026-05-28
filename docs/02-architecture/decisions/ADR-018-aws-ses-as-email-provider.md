# ADR-018: AWS SES as Email Provider

- Status: Accepted
- Date: 05-16-2026
- Tags: email, infrastructure, aws

## Context

The platform sends transactional emails: enrollment confirmation, certificate issuance notification, password reset, and event reminders. The email provider must be reliable, cost-effective at moderate volumes, and compatible with the existing AWS deployment.

## Decision

AWS Simple Email Service (SES) will be the transactional email provider.

Integration details:
- Emails are sent asynchronously via Celery tasks (ADR-014); the API never blocks on email delivery.
- `boto3` is used to call the SES `send_email` / `send_templated_email` API.
- SES templates are used for consistent, maintainable email formatting.
- Bounce and complaint handling is configured via SES event notifications to SNS, with a handler that marks email addresses as suppressed.
- DKIM, SPF, and DMARC are configured for the sending domain before production launch to maximize deliverability.
- SES starts in sandbox mode during development and is moved to production access before v1 launch.

## Consequences

**Positive:**
- SES pricing is among the lowest in the market at moderate volumes.
- Already within the AWS ecosystem; IAM policies control access without separate API key management.
- High deliverability with proper DKIM/SPF/DMARC configuration.
- `boto3` is already a project dependency for S3 (ADR-020); no additional SDK.

**Negative:**
- SES sandbox restrictions (verified recipients only) must be managed during development and testing.
- SES is an AWS-specific service; migrating to another provider would require swapping the sending integration (isolated to a single service class).
- Bounce handling requires SES → SNS → application webhook configuration, adding setup complexity.

**Neutral:**
- Email sending is abstracted behind an `EmailService` interface; swapping SES for another provider only requires replacing the concrete implementation.

## Alternatives Considered

**SendGrid:** Better deliverability tooling and analytics, but higher cost and a separate vendor relationship outside AWS. Rejected in favor of AWS ecosystem consistency.

**Mailgun:** Similar to SendGrid. Same reasoning. Rejected.

**SMTP (self-hosted Postfix):** Maximum control but high operational cost for maintaining deliverability (IP reputation, bounce management). Rejected.

## Links

- Related: ADR-014 (Celery), ADR-020 (S3/AWS)