# Urban Energy — EV Charging Management Platform

Our own CSMS + management dashboard, gradually replacing the Evoltsoft
("Urban Energy") vendor platform. Built to production standards (typed, tested,
layered) for a phased, strangler-fig migration.

## Structure

| Folder | What |
|--------|------|
| `backend/` | FastAPI management API — layered Ports & Adapters (`seed` \| `evoltsoft` \| `native`), SQLAlchemy + Alembic, structured logging, RBAC. See `backend/README.md`. |
| `frontend/` | React + Vite dashboard, Hebrew RTL, TACT design (analytics, partners, locations, sessions, billing). |
| `csms/` | OCPP 1.6J CSMS proof-of-concept (the charger-facing server). |
| `reference/` | Reverse-engineering notes (`URBANENERGY_REFERENCE.md`). Raw HAR captures are git-ignored. |

## Architecture

The dashboard reads through a stable **data-source port**. The Evoltsoft
integration is one removable adapter behind it — selected by `UE_DATA_SOURCE`.
When the migration to our own CSMS + Priority completes, that adapter is deleted
and nothing else changes.

```
chargers ──OCPP──▶ csms/        frontend ──REST──▶ backend (api → services → domain ports)
                                                              ↳ adapters: seed | evoltsoft | native
                                                              ↳ db (Postgres/SQLite + Alembic)
```

## Run (dev)

```bash
# backend  (http://localhost:8060)
cd backend && python -m uvicorn app.main:app --port 8060
# frontend (http://localhost:5173)
cd frontend && npm install && npm run dev
```

Configuration is via env (`UE_*`); copy `backend/.env.example` to `backend/.env`.
Secrets never live in the repo.
