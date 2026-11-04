.PHONY: install dev test lint fmt build build-backend build-frontend up down logs clean

install:
	pip install -e ".[dev,auto]"
	cd frontend && npm ci

dev:
	uvicorn risk_dashboard.api.main:app --reload --app-dir src --host 0.0.0.0

dev-frontend:
	cd frontend && npm run dev

test:
	python scripts/qa/run_isolated_tests.py -- --tb=short

test-cov:
	python scripts/qa/run_isolated_tests.py -- --cov=risk_dashboard --cov-report=term-missing --cov-report=html

lint:
	ruff check src/ tests/
	cd frontend && npm run lint

fmt:
	ruff format src/ tests/
	ruff check --fix src/ tests/

build: build-backend build-frontend

build-backend:
	PYTHONPATH=src PYTHONPYCACHEPREFIX=.local-dev/pycache python3 -m compileall -q src/risk_dashboard

build-frontend:
	cd frontend && npm run build

docker-build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f app

clean:
	find src tests scripts -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf output frontend/output build htmlcov .coverage coverage test-results playwright-report
	rm -rf .local-dev/.pytest_cache .local-dev/.ruff_cache .local-dev/.pycache_tmp .local-dev/pycache
