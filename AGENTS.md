# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project

Marko is a CommonMark-compliant Markdown parser for Python. Source lives in
`marko/`, tests in `tests/`, docs in `docs/`.

## Development

- Install dependencies: `pdm install -d`
- Run tests: `pdm run pytest tests/` (or `nox -s tests` for all Python versions)
- Lint and format: `pre-commit run --all-files` (black, isort, flake8, mypy)

## Pull requests

- Every PR **must pass Human Attestation verification** before it can be
  merged. Do not merge, or ask for a merge of, a PR whose Human Attestation
  check is missing or failing.
