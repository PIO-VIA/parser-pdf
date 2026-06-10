.PHONY: dev build up down migrate logs shell revision test format

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

migrate:
	alembic upgrade head

revision:
	alembic revision --autogenerate -m "$(msg)"

logs:
	docker-compose logs -f api

shell:
	docker-compose exec api bash

test:
	pytest tests/ -v

format:
	black app/ tests/
	isort app/ tests/
