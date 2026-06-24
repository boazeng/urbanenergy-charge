# Urban Energy backend — production image.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first (better layer caching).
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .

EXPOSE 8060

# 2 Uvicorn workers is plenty for a read-through dashboard; bump if needed.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8060", "--workers", "2"]
