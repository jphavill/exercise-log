.PHONY: up down logs rebuild rebuild-backend rebuild-frontend migrate seed test test-backend test-frontend prune-test-cache deploy

export DOCKER_BUILDKIT := 1
export COMPOSE_DOCKER_CLI_BUILD := 1

COMPOSE := docker compose
COMPOSE_LOCAL := docker compose -f docker-compose.local.yml
VENV_ACTIVATE ?= .venv/bin/activate

SERVICE ?= all
BACKEND_MODE ?= host
FRONTEND_MODE ?= local
BACKEND_PYTEST_ARGS ?=
BACKEND_BUILD ?= 0
FRONTEND_TEST_ARGS ?=

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
	@if [ "$(SERVICE)" = "backend" ]; then \
		$(MAKE) --no-print-directory test-backend BACKEND_MODE="$(BACKEND_MODE)" BACKEND_PYTEST_ARGS="$(BACKEND_PYTEST_ARGS)"; \
	elif [ "$(SERVICE)" = "frontend" ]; then \
		$(MAKE) --no-print-directory test-frontend FRONTEND_MODE="$(FRONTEND_MODE)" FRONTEND_TEST_ARGS="$(FRONTEND_TEST_ARGS)"; \
	elif [ "$(SERVICE)" = "all" ]; then \
		$(MAKE) --no-print-directory test-backend BACKEND_MODE="$(BACKEND_MODE)" BACKEND_PYTEST_ARGS="$(BACKEND_PYTEST_ARGS)" && \
		$(MAKE) --no-print-directory test-frontend FRONTEND_MODE="$(FRONTEND_MODE)" FRONTEND_TEST_ARGS="$(FRONTEND_TEST_ARGS)"; \
	else \
		echo "Invalid SERVICE='$(SERVICE)'. Use backend, frontend, or all."; \
		exit 1; \
	fi

test-backend:
	@if [ "$(BACKEND_MODE)" = "host" ]; then \
		. "$(VENV_ACTIVATE)" && pytest backend $(BACKEND_PYTEST_ARGS); \
	elif [ "$(BACKEND_MODE)" = "container" ]; then \
		SOURCE_HASH="$$( { git rev-parse HEAD:backend 2>/dev/null || printf no-head; git status --porcelain -- backend; } | shasum -a 256 | awk '{print $$1}' )"; \
		IMAGE_ID="$$( $(COMPOSE) config --images 2>/dev/null | awk '/backend$$/ {print; exit}' )"; \
		IMAGE_HASH=""; \
		if [ -n "$$IMAGE_ID" ]; then \
			IMAGE_HASH="$$(docker image inspect "$$IMAGE_ID" --format '{{ index .Config.Labels "com.exercise.backend-source-hash" }}' 2>/dev/null || true)"; \
		fi; \
		if [ "$(BACKEND_BUILD)" = "1" ] || [ "$$IMAGE_HASH" != "$$SOURCE_HASH" ]; then \
			$(COMPOSE) build --build-arg BACKEND_SOURCE_HASH="$$SOURCE_HASH" backend; \
		fi; \
		$(COMPOSE) run --rm -e DATABASE_URL=sqlite:////tmp/backend_test.sqlite3 -e AUTO_SEED=false backend pytest $(BACKEND_PYTEST_ARGS); \
	else \
		echo "Invalid BACKEND_MODE='$(BACKEND_MODE)'. Use host or container."; \
		exit 1; \
	fi

test-frontend:
	@if [ "$(FRONTEND_MODE)" = "local" ]; then \
		cd frontend && npm test -- $(FRONTEND_TEST_ARGS); \
	elif [ "$(FRONTEND_MODE)" = "cached" ]; then \
		docker compose -f docker-compose.yml run --rm --build frontend-test $(FRONTEND_TEST_ARGS); \
	else \
		echo "Invalid FRONTEND_MODE='$(FRONTEND_MODE)'. Use local or cached."; \
		exit 1; \
	fi

prune-test-cache:
	./scripts/prune-test-caches.sh

deploy:
	bash scripts/deploy-prod.sh
