# Setup and Run Guide

## Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/)
- Supabase project (PostgreSQL connection URL)
- Optional but recommended: [Ollama](https://ollama.com/) running locally (default provider + embeddings)

## Installation (uv)

```bash
export UV_PROJECT_ENVIRONMENT=rag
uv sync
```

This creates and uses a project virtual environment at `./rag`.

## Environment Variables

Copy and edit `.env.example`.

```env
APP_NAME=RAG Chatbot
APP_HOST=0.0.0.0
APP_PORT=8000
UV_PROJECT_ENVIRONMENT=rag
SUPABASE_DB_URL=postgresql+psycopg://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres?sslmode=require
DATABASE_URL=
MAX_UPLOAD_SIZE_MB=20
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text
```

Notes:
- `SUPABASE_DB_URL` is preferred and used first.
- `DATABASE_URL` is fallback.

## Supabase Connection Steps

1. In Supabase dashboard, open `Project Settings` -> `Database`.
2. Copy the Postgres connection string.
3. Paste it into `SUPABASE_DB_URL`.
4. Keep `sslmode=require` in the URL.

## Start Application

```bash
export UV_PROJECT_ENVIRONMENT=rag
uv run python run.py
```

App URL: `http://localhost:8000`

## Ollama First-Time Commands

```bash
ollama serve
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

## Troubleshooting

- `psycopg` connection errors:
  - Verify `SUPABASE_DB_URL` and ensure DB password is correct.
- Upload/index errors mentioning embeddings:
  - Ensure Ollama is running and `OLLAMA_EMBED_MODEL` is pulled.
- Chat says vector DB is empty:
  - Upload documents from Data Management.
- Provider key errors:
  - Save one API key for the selected provider in Settings.
