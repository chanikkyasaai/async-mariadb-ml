# Contributing to async-mariadb-connector

Thanks for your interest in contributing! We welcome bug reports, feature requests, docs improvements, and code.

## Getting started

1. Fork the repo and create a feature branch.
2. Create a Python 3.9+ environment and install deps:
   ```bash
   pip install -e ".[dev]"
   ```
3. Run MariaDB locally (see `docker-compose.yml` or use your own instance) and set `.env` (copy `.env.example`).
4. Run tests:
   ```bash
   pytest -q
   ```

## Code style
- Use Black, isort, flake8, and mypy (enforced in CI soon). Keep functions small and well-documented.
- Write or update tests for each change. Aim to keep coverage from regressing.

## Commit and PR
- Use clear, descriptive commit messages.
- Open a PR against `main` with a concise description, screenshots/logs when helpful, and checklists for tests/docs.

## Security
If you find a security issue, please email the maintainer instead of opening a public issue.

## License
By contributing, you agree your contributions are licensed under the MIT License.
