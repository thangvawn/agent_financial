.PHONY: install dev test lint fmt build up down logs clean

install:
	pip install -e ".[dev,auto]"
	cd frontend && npm ci

dev:
	uvicorn risk_dashboard.api.main:app --reload --app-dir src

dev-frontend:
	cd frontend && npm run dev

test:
	pytest --tb=short -q

test-cov:
	pytest --cov=risk_dashboard --cov-report=term-missing --cov-report=html

lint:
	ruff check src/ tests/
	cd frontend && npm run lint

fmt:
	ruff format src/ tests/
	ruff check --fix src/ tests/

build:
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
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov .coverage
