.PHONY: up down logs rebuild rebuild-backend rebuild-frontend migrate seed test deploy

COMPOSE := docker compose
COMPOSE_LOCAL := docker compose -f docker-compose.local.yml

up:
	$(COMPOSE_LOCAL) up -d

down:
	$(COMPOSE_LOCAL) down

logs:
	$(COMPOSE_LOCAL) logs -f

rebuild:
	$(COMPOSE_LOCAL) up -d --build

rebuild-backend:
	$(COMPOSE_LOCAL) up -d --build backend

rebuild-frontend:
	$(COMPOSE_LOCAL) up -d --build frontend

migrate:
	$(COMPOSE_LOCAL) exec backend alembic upgrade head

seed:
	$(COMPOSE_LOCAL) exec backend python seed.py

test:
	. /Users/jphavill/Documents/github/exercise-log/.venv/bin/activate && pytest backend

deploy:
	bash scripts/deploy-prod.sh
