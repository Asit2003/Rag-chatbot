# Setup and Run Guide

## Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/)
- Supabase project (PostgreSQL connection URL)
- Supabase Storage bucket for documents (recommended for production)
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
MAX_UPLOAD_SIZE_MB=20
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=bge-m3
DOC_STORAGE_BACKEND=
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_STORAGE_BUCKET=documents
SUPABASE_STORAGE_PREFIX=documents
```

Notes:
- `SUPABASE_DB_URL` is required (Supabase-only).
- Settings and API keys are stored in `data/config/settings.json`.
- If `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are set, document storage uses Supabase Storage by default.
- Set `DOC_STORAGE_BACKEND=local` to force local file storage.

## Supabase Connection Steps

1. In Supabase dashboard, open `Project Settings` -> `Database`.
2. Copy the Postgres connection string.
3. Paste it into `SUPABASE_DB_URL`.
4. Keep `sslmode=require` in the URL.

## Supabase Storage Steps (Documents)

1. In Supabase dashboard, open `Storage`.
2. Create a bucket (default: `documents`).
3. Create a service role key and set `SUPABASE_SERVICE_ROLE_KEY`.
4. Set `SUPABASE_URL`, `SUPABASE_STORAGE_BUCKET`, and optional `SUPABASE_STORAGE_PREFIX`.

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
ollama pull bge-m3
```

## Model Recommendations

- Default chat model: `llama3.1:8b` for a strong quality/speed balance on local hardware.
- GPU-heavy option: `llama3.1:70b` for higher quality when you have the resources.
- Embeddings: `bge-m3` for robust multilingual retrieval.

## Troubleshooting

- `psycopg` connection errors:
  - Verify `SUPABASE_DB_URL` and ensure DB password is correct.
- Upload/index errors mentioning embeddings:
  - Ensure Ollama is running and `OLLAMA_EMBED_MODEL` is pulled (`bge-m3` recommended).
- Chat says vector DB is empty:
  - Upload documents from Data Management.
- Provider key errors:
  - Save one API key for the selected provider in Settings.
