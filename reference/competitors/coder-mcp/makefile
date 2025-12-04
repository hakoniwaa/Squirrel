# Makefile for MCP Server Testing

.PHONY: help test test-unit test-integration test-e2e test-performance test-all coverage lint format clean install

# Default target
help:
	@echo "MCP Server Test Suite Commands:"
	@echo "  make install          - Install all dependencies including test dependencies"
	@echo "  make test            - Run all tests with coverage"
	@echo "  make test-unit       - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-e2e        - Run end-to-end tests only"
	@echo "  make test-performance - Run performance tests"
	@echo "  make test-watch      - Run tests in watch mode"
	@echo "  make coverage        - Generate coverage report"
	@echo "  make lint            - Run all linters"
	@echo "  make format          - Format code"
	@echo "  make clean           - Clean up test artifacts"
	@echo "  make test-failed     - Re-run only failed tests"
	@echo "  make test-parallel   - Run tests in parallel"
	@echo "  make test-debug      - Run tests with debugging enabled"

# Install dependencies
install:
	poetry install --with test,dev
	poetry run pre-commit install

# Run all tests with coverage
test:
	poetry run pytest \
		--cov=coder_mcp \
		--cov-report=term-missing \
		--cov-report=html:reports/coverage \
		--cov-report=xml:reports/coverage.xml \
		--cov-fail-under=80 \
		-v

# Run unit tests only
test-unit:
	poetry run pytest tests/unit \
		--cov=coder_mcp \
		--cov-report=term-missing \
		-v

# Run integration tests
test-integration:
	docker-compose -f tests/docker-compose.yml up -d
	poetry run pytest tests/integration \
		--cov=coder_mcp \
		--cov-report=term-missing \
		-v
	docker-compose -f tests/docker-compose.yml down

# Run end-to-end tests
test-e2e:
	docker-compose -f tests/docker-compose.yml up -d
	poetry run pytest tests/e2e \
		--cov=coder_mcp \
		--cov-report=term-missing \
		-v
	docker-compose -f tests/docker-compose.yml down

# Run performance tests
test-performance:
	poetry run pytest tests/performance \
		--benchmark-only \
		--benchmark-json=reports/benchmark.json \
		--benchmark-autosave \
		-v

# Run tests in watch mode
test-watch:
	poetry run ptw -- -v

# Run only failed tests from last run
test-failed:
	poetry run pytest --lf -v

# Run tests in parallel
test-parallel:
	poetry run pytest -n auto -v

# Run tests with debugging
test-debug:
	poetry run pytest --pdb -s -v

# Generate coverage report
coverage:
	poetry run pytest --cov=coder_mcp --cov-report=html:reports/coverage
	@echo "Coverage report generated at reports/coverage/index.html"
	@python -m webbrowser reports/coverage/index.html

# Run all linters
lint:
	@echo "Running Black..."
	poetry run black --check coder_mcp tests
	@echo "\nRunning isort..."
	poetry run isort --check-only coder_mcp tests
	@echo "\nRunning Flake8..."
	poetry run flake8 coder_mcp tests
	@echo "\nRunning mypy..."
	poetry run mypy coder_mcp
	@echo "\nRunning bandit..."
	poetry run bandit -r coder_mcp -ll
	@echo "\nRunning pylint..."
	poetry run pylint coder_mcp

# Format code
format:
	poetry run black coder_mcp tests
	poetry run isort coder_mcp tests
	poetry run autoflake --in-place --remove-all-unused-imports -r coder_mcp tests

# Clean test artifacts
clean:
	rm -rf .pytest_cache
	rm -rf reports/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Run security checks
security:
	poetry run safety check
	poetry run bandit -r coder_mcp -ll
	poetry run pip-audit

# Run mutation testing
test-mutation:
	poetry run mutmut run --paths-to-mutate=coder_mcp/
	poetry run mutmut html

# Generate test report
test-report:
	poetry run pytest \
		--html=reports/test-report.html \
		--self-contained-html \
		--junit-xml=reports/junit.xml \
		-v

# Run specific test file
test-file:
	@read -p "Enter test file path: " filepath; \
	poetry run pytest $$filepath -v

# Run tests with specific marker
test-mark:
	@read -p "Enter test marker (e.g., slow, integration): " marker; \
	poetry run pytest -m $$marker -v

# Profile test execution
test-profile:
	poetry run pytest --profile-svg -v
	@echo "Profile saved to prof/combined.svg"

# Docker commands for testing
docker-up:
	docker-compose -f tests/docker-compose.yml up -d

docker-down:
	docker-compose -f tests/docker-compose.yml down

docker-logs:
	docker-compose -f tests/docker-compose.yml logs -f

# CI simulation
ci:
	@echo "Simulating CI pipeline..."
	make lint
	make test-unit
	make test-integration
	make test-e2e
	make security
	@echo "CI pipeline complete!"

# Pre-commit checks
pre-commit:
	poetry run pre-commit run --all-files

# Update test snapshots
test-update-snapshots:
	poetry run pytest --snapshot-update

# Test coverage by file
coverage-by-file:
	poetry run pytest --cov=coder_mcp --cov-report=term-missing:skip-covered
	poetry run coverage report --sort=cover

# Continuous test runner for development
dev-test:
	poetry run ptw -- -x -v --tb=short

# Run tests with different Python versions using tox
test-all-python:
	poetry run tox

# Benchmark comparison
benchmark-compare:
	poetry run pytest-benchmark compare reports/benchmark*.json

# Create test database with sample data
test-db-setup:
	poetry run python tests/scripts/setup_test_db.py

# Quick smoke test
smoke-test:
	poetry run pytest -k "smoke" -v --tb=short

.DEFAULT_GOAL := help
