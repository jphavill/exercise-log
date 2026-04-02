# NFC Micro Exercise Tracker

A Docker-based exercise logging stack with Angular frontend, FastAPI backend, PostgreSQL, and Caddy reverse proxy.

## Prerequisites

- Docker
- Docker Compose
- Python 3.12+ and project virtualenv at `.venv` (for host-based backend work)
- Node.js 22+ (for local frontend development without Docker)

## Setup

1. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Install backend dependencies (host mode):
   ```bash
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   ```

3. Optional: override compose defaults via environment variables:
   - `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB`
   - `AUTO_SEED` (`true`/`false`)

## Quick Start

### Local Development (fastest iteration)

```bash
# Terminal 1: backend
source .venv/bin/activate
cd backend
alembic -c alembic.ini upgrade head
python seed.py
uvicorn app.main:app --reload

# Terminal 2: frontend
cd frontend
npm start
# Access at http://localhost:4200
```

### With Docker (full stack)

```bash
# Local stack (recommended for day-to-day)
docker compose -f docker-compose.local.yml up -d --build

# Production-like stack
docker compose up -d --build
```

Access at:
- `http://localhost:8003`

## Routes

- `/` -> Angular app
- `/api/*` -> FastAPI API

## Running the Project

### Local Docker mode

```bash
docker compose -f docker-compose.local.yml up -d
```

This starts:
- Frontend container
- Backend container (`uvicorn --reload`)
- PostgreSQL
- Caddy (on port `8003`)

### Production compose mode

```bash
docker compose up -d
```

Use `scripts/deploy-prod.sh` for the full deploy flow (pull latest main, run tests, back up DB, rebuild/restart stack).

## Common Commands

```bash
# Start local stack
docker compose -f docker-compose.local.yml up -d

# View logs
docker compose -f docker-compose.local.yml logs -f

# Stop local stack
docker compose -f docker-compose.local.yml down

# Rebuild all services
docker compose -f docker-compose.local.yml up -d --build

# Rebuild backend only
docker compose -f docker-compose.local.yml up -d --build backend

# Rebuild frontend only
docker compose -f docker-compose.local.yml up -d --build frontend
```

## Database Migrations (Alembic)

Alembic config is in `backend/alembic.ini` and revisions are in `backend/alembic/versions/`.

```bash
# Preferred in local Docker mode
make migrate

# Or directly in the container
docker compose -f docker-compose.local.yml exec backend alembic -c alembic.ini upgrade head

# Host-based option
source .venv/bin/activate
cd backend
alembic -c alembic.ini upgrade head

# Create a new migration
alembic -c alembic.ini revision --autogenerate -m "describe change"
```

## Running Tests

### Backend tests (pytest)

```bash
source .venv/bin/activate
cd backend
pytest
```

Run a single backend file:

```bash
cd backend
pytest tests/test_api.py
```

### Frontend tests (Vitest)

```bash
cd frontend
npm test
```

Watch mode:

```bash
cd frontend
npm run test:watch
```

Run a single frontend spec file:

```bash
cd frontend
npm test -- src/app/shared/value-format.spec.ts
```

## Seeded Exercises

- `l-sit` (`duration_seconds`)
- `pullups` (`reps`)
- `weighted-pullups` (`reps_plus_weight_lbs`)
- `mace-swings` (`reps`)

## iPhone NFC Shortcut Flows

See `SHORTCUTS.md` for the NFC/iPhone automation payloads and workflow details.

## Makefile Shortcuts

```bash
make up
make logs
make down
make rebuild
make rebuild-backend
make rebuild-frontend
make migrate
make seed
make test
make deploy
```
