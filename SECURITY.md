# Security Policy

## Reporting a vulnerability

If you found a security vulnerability, **do not open a public issue**.

Send an email to: security@digital-institute.com (or the maintainer's email)

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)

You will receive a response within 72 hours.

## Repository security practices

- Credentials are never committed — use environment variables
- The `.env` file is listed in `.gitignore`
- Production secrets are stored outside the codebase (AWS SSM / Secrets Manager)
- Dependencies are audited regularly
- Passwords are stored with argon2 (never in plain text)