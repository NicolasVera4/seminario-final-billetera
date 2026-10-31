.PHONY: up down test test-back test-front test-int migrar seed

up:
	docker compose up --build

down:
	docker compose down

test: test-back test-front

test-back:
	cd backend && . .venv/bin/activate && python -m pytest tests/ -m "not integracion"

test-front:
	cd frontend && npm test

test-int:
	cd backend && . .venv/bin/activate && python -m pytest tests/ -m integracion

migrar:
	cd backend && . .venv/bin/activate && alembic upgrade head

seed:
	cd backend && . .venv/bin/activate && python -m app.seed
