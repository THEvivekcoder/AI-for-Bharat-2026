.PHONY: help install test lint format clean build deploy

help:
	@echo "BharatSahayak - Development Commands"
	@echo ""
	@echo "install     Install dependencies"
	@echo "test        Run all tests"
	@echo "lint        Run linters"
	@echo "format      Format code"
	@echo "clean       Clean build artifacts"
	@echo "build       Build SAM application"
	@echo "deploy      Deploy to AWS"
	@echo "local-api   Start local API server"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	pytest

test-unit:
	pytest tests/unit/

test-integration:
	pytest tests/integration/

test-property:
	pytest tests/property/

lint:
	flake8 src/ tests/
	pylint src/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

clean:
	rm -rf .aws-sam/
	rm -rf build/
	rm -rf dist/
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:
	sam build

validate:
	sam validate --lint

deploy:
	bash infrastructure/scripts/deploy.sh dev

deploy-staging:
	bash infrastructure/scripts/deploy.sh staging

deploy-prod:
	bash infrastructure/scripts/deploy.sh prod

local-api:
	sam local start-api

local-invoke:
	sam local invoke $(FUNCTION) -e events/$(EVENT).json
