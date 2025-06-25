# Makefile for video transcriber project

.PHONY: help install install-dev test test-unit test-integration test-coverage lint format clean pre-commit benchmark

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt -r requirements-dev.txt
	pre-commit install

test: ## Run all tests
	pytest tests/ -v

test-unit: ## Run unit tests only
	pytest tests/unit -v --tb=short

test-integration: ## Run integration tests only
	pytest tests/integration -v --tb=short

test-coverage: ## Run tests with coverage report
	pytest tests/unit tests/integration --cov=src --cov-report=html --cov-report=term-missing --cov-fail-under=80

benchmark: ## Run performance benchmarks
	pytest tests/benchmarks -v --benchmark-only

lint: ## Run linting checks
	black --check src/ tests/
	isort --check-only src/ tests/
	flake8 src/ tests/
	mypy src/ --ignore-missing-imports

format: ## Format code with black and isort
	black src/ tests/
	isort src/ tests/

pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

clean: ## Clean up temporary files and caches
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf .mypy_cache
	rm -rf .tox
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

setup-dev: install-dev ## Set up development environment
	@echo "Development environment setup complete!"
	@echo "Run 'make test' to verify everything is working."

ci: lint test-coverage ## Run CI pipeline locally
	@echo "CI pipeline completed successfully!"

# Docker commands
docker-build: ## Build Docker image
	docker build -t video-transcriber .

docker-run: ## Run application in Docker container
	docker run -p 5001:5001 video-transcriber

# Development server
dev: ## Run development server
	python main.py

# Production commands
prod-install: ## Install for production
	pip install -r requirements.txt --no-dev

security-check: ## Run security checks
	bandit -r src/ -f json -o bandit-report.json
	@echo "Security check completed. See bandit-report.json for details."
