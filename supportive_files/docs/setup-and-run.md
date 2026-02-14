# Setup and Run Guide

## Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/)
- Supabase project (PostgreSQL connection URL). This is required.
- Supabase Storage bucket for documents (optional; local storage works if not configured)
- Optional: [Ollama](https://ollama.com/) running locally (default chat provider)

## Installation (uv)

```bash
uv sync
```

This creates and uses a project virtual environment at `./.venv`.

## Installation (any venv)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

## Environment Variables

Copy and edit `.env.example`.

```env
APP_NAME=RAG Chatbot
APP_HOST=0.0.0.0
APP_PORT=8000
SUPABASE_DB_URL=postgresql+psycopg://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres?sslmode=require
MAX_UPLOAD_SIZE_MB=200
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=bge-m3
GEMINI_EMBED_MODEL=gemini-embedding-001
OPENAI_EMBED_MODEL=text-embedding-3-large
DOC_STORAGE_BACKEND=
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_STORAGE_BUCKET=documents
SUPABASE_STORAGE_PREFIX=documents
```

Notes:
- `SUPABASE_DB_URL` is required (Supabase-only).
- Settings and API keys are stored in `data/config/settings.json`.
- Document storage uses Supabase Storage when `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are set. Otherwise it uses local storage.
- Set `DOC_STORAGE_BACKEND=local` or `DOC_STORAGE_BACKEND=supabase` to force a backend.
- Embeddings and retrieval require an OpenAI API key saved in Settings.
- If `MAX_UPLOAD_SIZE_MB` is not set, the default is 20 MB.

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
uv run python run.py
```

App URL: `http://localhost:8000`

## Ollama First-Time Commands

```bash
ollama serve
ollama pull llama3.1:8b
```

## Model Recommendations

- Default chat model: `llama3.1:8b` for a strong quality/speed balance on local hardware.
- GPU-heavy option: `llama3.1:70b` for higher quality when you have the resources.
- Embeddings: `text-embedding-3-large` via OpenAI API key.

## Troubleshooting

- `psycopg` connection errors:
  - Verify `SUPABASE_DB_URL` and ensure DB password is correct.
- Upload/index errors mentioning embeddings:
  - Save an OpenAI API key in Settings (used for embeddings).
- Chat says vector DB is empty:
  - Upload documents from Data Management.
- Provider key errors:
  - Save one API key for the selected provider in Settings.
