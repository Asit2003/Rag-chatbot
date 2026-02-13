# Cloud Deployment Guide (Separate Containers)

This mode runs app and PostgreSQL as separate containers.

## 1. Configure Environment

Edit `.env` with secure values:

```env
POSTGRES_DB=ragchat
POSTGRES_USER=ragchat
POSTGRES_PASSWORD=change-this
UV_PROJECT_ENVIRONMENT=rag
SUPABASE_DB_URL=
DATABASE_URL=postgresql+psycopg://ragchat:change-this@postgres:5432/ragchat
APP_HOST=0.0.0.0
APP_PORT=8000
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_EMBED_MODEL=nomic-embed-text
```

Notes:
- Leave `SUPABASE_DB_URL` empty for local postgres-container mode.
- If `SUPABASE_DB_URL` is set, app will prefer it over `DATABASE_URL`.

## 2. Start Stack

Use `docker-compose.separate.yml`:

```bash
docker compose -f docker-compose.separate.yml up -d --build
```

## 3. Verify

- App: `http://localhost:8000`
- PostgreSQL is internal (`postgres:5432`) and not exposed publicly.

## 4. Production Hardening

- Use managed secret injection instead of plaintext `.env`.
- Restrict PostgreSQL network access.
- Enable automated backups for PostgreSQL volume.
- Store `/app/data` on durable volume.

## Scale Option

You can replace the `postgres` service with Supabase by setting only `SUPABASE_DB_URL` in the app container environment.
