.PHONY: help install dev db-up db-down db-init test clean

help:
	@echo "BharatSahayak - Development Commands"
	@echo ""
	@echo "  make install    - Install dependencies"
	@echo "  make dev        - Run development server"
	@echo "  make db-up      - Start PostgreSQL and Redis"
	@echo "  make db-down    - Stop PostgreSQL and Redis"
	@echo "  make db-init    - Initialize database tables"
	@echo "  make test       - Run setup validation tests"
	@echo "  make clean      - Clean up cache files"

install:
	pip install -r requirements.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

db-up:
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 5

db-down:
	docker-compose down

db-init:
	python scripts/init_db.py

test:
	python scripts/test_setup.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
