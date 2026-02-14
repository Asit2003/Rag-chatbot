FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_PROJECT_ENVIRONMENT=rag
ENV UV_LINK_MODE=copy

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9.29 /uv /usr/local/bin/uv
COPY --from=ghcr.io/astral-sh/uv:0.9.29 /uvx /usr/local/bin/uvx

COPY pyproject.toml uv.toml /app/
RUN uv sync --no-dev

COPY . /app

RUN mkdir -p /app/data/uploads /app/data/chroma /app/data/secrets /app/data/config

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
