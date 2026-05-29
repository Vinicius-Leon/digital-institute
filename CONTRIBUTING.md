# Contributing

## Environment setup

Follow the README to run the project locally.

## Branch naming

- `main` — production, protected
- `develop` — integration
- `feat/feature-name` — new features
- `fix/bug-name` — bug fixes
- `chore/what-it-is` — configuration, infra, dependencies
- `docs/what-it-is` — documentation

## Commits

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` new feature
- `fix:` bug fix
- `chore:` configuration, dependencies, infra
- `docs:` documentation
- `test:` tests
- `refactor:` refactoring without behavior change

Example: `feat: add user registration endpoint`

## Pull Requests

1. Create a branch from `develop`
2. Make small, descriptive commits
3. Open the PR targeting `develop`
4. Fill in the PR template
5. Wait for CI to pass before requesting a review

## Running quality checks before committing

```bash
ruff check src/ tests/
black src/ tests/
mypy src/
pytest tests/unit/ -m unit
```

## Project structure
