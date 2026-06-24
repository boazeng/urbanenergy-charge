# Urban Energy — Backend

Production-grade foundation (Phase 0) for the EV-charging management platform.

## Architecture (Ports & Adapters / layered)

```
app/
  api/         HTTP edge — routes, request/response schemas, DI       (knows: services)
  services/    application logic (clamping, aggregation, caching)     (knows: ports)
  domain/      models + ports (the stable interfaces)                 (knows: nothing)
  adapters/    implementations of the ports:
    seed/        deterministic dev/test data            ← active now
    evoltsoft/   removable mirror of the vendor API     ← Phase 1
    native/      our own CSMS + Priority                ← later
  db/          SQLAlchemy engine + ORM models (synced/native data lands here)
  core/        config, structured logging, security
```

**Why this shape:** the core depends only on `domain/ports.py`. The Evoltsoft
integration is one adapter behind that port — when migration finishes we delete
`adapters/evoltsoft/` and its env vars, and nothing else changes. The data source
is chosen by `UE_DATA_SOURCE` (`seed` | `evoltsoft` | `native`).

## Run (dev)

```bash
# from repo root, using the shared venv
../.venv/Scripts/python -m pip install -e ".[dev]"   # first time
cp .env.example .env                                  # adjust if needed
alembic upgrade head                                  # create DB schema
../.venv/Scripts/python -m uvicorn app.main:app --port 8060 --reload
```

API: http://localhost:8060/api  ·  docs: http://localhost:8060/docs

## Quality gates (also run in CI)

```bash
ruff check . && ruff format --check .   # lint + format
mypy app                                # strict typing
pytest                                  # tests
```

## Config

All via env (prefix `UE_`), read from the shared `env/.env` then a local `.env`.
See `.env.example`. Production sets `UE_ENV=prod`, a PostgreSQL `UE_DATABASE_URL`,
`UE_AUTH_MODE=oauth`, and `UE_SENTRY_DSN`.

## Observability & security (baseline)

- **Logging:** structured JSON, one line per event, with a per-request
  `x-request-id` correlation id (also returned as a response header).
- **Health:** `/api/health` (liveness) · `/api/ready` (readiness — checks the
  data source). `sync_runs` table audits every future sync job.
- **Errors:** unhandled exceptions are logged server-side and return a generic
  500 (no internal leakage); optional Sentry via `UE_SENTRY_DSN`.
- **Security:** `Role`-based access (`require_role`), dev/oauth auth backends;
  `dev` auth is hard-blocked in production.

## Migrations

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```
