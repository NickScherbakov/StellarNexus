.PHONY: help install test lint format check pre-commit clean dev build

# Default target
help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

# Development setup
install: ## Install development dependencies
	pip install -r scripts/requirements.txt
	pip install pytest pytest-cov black flake8 pre-commit
	pre-commit install

dev-install: ## Install development dependencies (alias for install)
	$(MAKE) install

# Code formatting and linting
format: ## Format code with black
	black scripts/ tests/ api/ *.py

lint: ## Run linting with flake8
	flake8 scripts/ tests/ api/ *.py

check: ## Run both linting and formatting checks
	black --check scripts/ tests/ api/ *.py
	flake8 scripts/ tests/ api/ *.py

# Testing
test: ## Run tests with pytest
	python -m pytest tests/ -v

test-cov: ## Run tests with coverage
	python -m pytest tests/ -v --cov=scripts --cov=api --cov-report=html --cov-report=term

test-integration: ## Run integration tests
	python -m pytest tests/integration/ -v

# Pre-commit
pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

pre-commit-update: ## Update pre-commit hooks
	pre-commit autoupdate

# Development server
serve: ## Start the web server for development
	python web_server.py

serve-api: ## Start the API server for development
	cd api && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Data operations
fetch-data: ## Fetch latest GitHub data
	cd scripts && python main.py

run-ml: ## Run ML predictions
	cd scripts && python ml_predictor.py

# Docker operations
docker-build: ## Build Docker image
	docker build -t stellarnexus:latest .

docker-run: ## Run Docker container
	docker-compose up -d

docker-stop: ## Stop Docker container
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

# Cleanup
clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage

clean-data: ## Clean generated data files
	rm -f data/*.json

# CI/CD helpers
ci-install: ## Install dependencies for CI
	pip install -r scripts/requirements.txt
	pip install pytest pytest-cov black flake8 pre-commit

ci-test: ## Run tests in CI environment
	python -m pytest tests/ -v --cov=scripts --cov=api --cov-report=xml --cov-report=term

ci-lint: ## Run linting in CI environment
	black --check scripts/ tests/ api/ *.py
	flake8 scripts/ tests/ api/ *.py

# Database operations
db-init: ## Initialize database
	cd scripts && python -c "import subprocess; subprocess.run(['psql', '-f', 'init.sql'])"

db-migrate: ## Run database migrations
	@echo "Database migrations would go here"

# Documentation
docs: ## Generate documentation
	@echo "Documentation generation would go here"

# All-in-one commands
setup: ## Complete development setup
	$(MAKE) install
	$(MAKE) pre-commit

check-all: ## Run all checks (lint, format, test)
	$(MAKE) check
	$(MAKE) test

build: ## Build and test everything
	$(MAKE) check-all
	$(MAKE) docker-build