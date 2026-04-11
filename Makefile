.PHONY: up down logs rebuild rebuild-backend rebuild-frontend migrate seed test deploy

export DOCKER_BUILDKIT := 1
export COMPOSE_DOCKER_CLI_BUILD := 1

COMPOSE := docker compose
COMPOSE_LOCAL := docker compose -f docker-compose.local.yml

up:
	$(COMPOSE_LOCAL) up -d

down:
	$(COMPOSE_LOCAL) down

logs:
	$(COMPOSE_LOCAL) logs -f

rebuild:
	$(COMPOSE_LOCAL) build --parallel
	$(COMPOSE_LOCAL) up -d
	$(MAKE) migrate

rebuild-backend:
	$(COMPOSE_LOCAL) build backend
	$(COMPOSE_LOCAL) up -d backend

rebuild-frontend:
	$(COMPOSE_LOCAL) build frontend
	$(COMPOSE_LOCAL) up -d frontend

migrate:
	$(COMPOSE_LOCAL) exec backend alembic upgrade head

seed:
	$(COMPOSE_LOCAL) exec backend python seed.py

test:
	. /Users/jphavill/Documents/github/exercise-log/.venv/bin/activate && pytest backend

deploy:
	bash scripts/deploy-prod.sh
