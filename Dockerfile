# Single-container image: build the React SPA, then serve it + the API from FastAPI.
# (Build context is the repo root.)

# ---- Stage 1: build the React dashboard ----
FROM node:22-alpine AS web
WORKDIR /web
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Python backend that also serves the built SPA ----
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# git is needed for the shared-auth git dependency.
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml ./
COPY backend/app ./app
RUN pip install --no-cache-dir .

COPY --from=web /web/dist ./static

EXPOSE 8060
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8060", "--workers", "2"]
