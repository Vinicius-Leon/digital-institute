# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Base project structure with FastAPI + SQLAlchemy + Alembic
- Authentication module with JWT + argon2
- `/health` endpoint with dependency status checks
- Docker Compose setup with api + postgres + redis + rabbitmq + worker
- Structured JSON logging with request_id
- CI pipeline with GitHub Actions (lint + types + tests)
- Repository documentation (README, CONTRIBUTING, SECURITY)
- ADRs for initial architectural decisions