.PHONY: up down test test-back test-front test-int test-e2e migrar seed seed-demo coverage

up:
	docker compose up --build

down:
	docker compose down

test: test-back test-front

test-back:
	cd backend && . .venv/bin/activate && python -m pytest tests/ -m "not integracion and not e2e"

test-front:
	cd frontend && npm test

test-int:
	cd backend && . .venv/bin/activate && python -m pytest tests/ -m integracion

test-e2e:
	cd backend && . .venv/bin/activate && python -m pytest tests/e2e/ -m e2e -s

migrar:
	cd backend && . .venv/bin/activate && alembic upgrade head

seed:
	cd backend && . .venv/bin/activate && python -m app.seed

seed-demo:
	cd backend && . .venv/bin/activate && python -m app.seed_demo

coverage:
	cd backend && . .venv/bin/activate && python -m pytest tests/ -m "not integracion and not e2e" --cov=app --cov-report=term-missing
