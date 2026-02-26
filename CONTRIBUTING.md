# Contributing to PerpCity Python SDK

Thanks for your interest in contributing! This document covers everything you need to get started.

## Prerequisites

- Python >= 3.10
- [Foundry](https://book.getfoundry.sh/) (for integration tests)

## Getting Started

```bash
git clone https://github.com/StrobeLabs/perpcity-python-sdk.git
cd perpcity-python-sdk
pip install -e ".[dev]"
```

## Development

```bash
# Run unit tests
make test

# Run integration tests (spawns Anvil automatically)
make test-integration

# Lint and format check
make lint

# Auto-format
make format

# Full CI check (lint + unit tests)
make ci
```

## Pull Requests

1. Fork the repo and create a branch from `main`
2. Write your code and add tests for new functionality
3. Run `make ci` to verify everything passes
4. Open a PR against `main`

## Code Style

- Follow [Ruff](https://docs.astral.sh/ruff/) formatting and linting rules (enforced by CI)
- Type hints encouraged
- Write tests using [pytest](https://pytest.org/)

## Reporting Issues

- Use the bug report template for bugs
- Use the feature request template for new features
- Include SDK version, Python version, and steps to reproduce

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
