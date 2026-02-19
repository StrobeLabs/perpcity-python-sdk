.PHONY: build test test-unit test-integration lint format ci

build:
	pip install -e ".[dev]"

test: test-unit

test-unit:
	pytest tests/unit -v

test-integration:
	pytest tests/integration -v -m integration

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

ci: lint test-unit
