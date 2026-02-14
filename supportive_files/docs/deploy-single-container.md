# Cloud Deployment Guide (Single Container)

This mode runs only the app container. PostgreSQL is external via Supabase.

## 1. Prepare Supabase Database URL

From Supabase dashboard (`Project Settings` -> `Database`), copy the Postgres connection string and keep `sslmode=require`.

## 2. Build Docker Image

```bash
docker build -t rag-chatbot:latest .
```

## 3. Push Image to Registry

Example (Docker Hub):

```bash
docker tag rag-chatbot:latest <dockerhub-user>/rag-chatbot:latest
docker push <dockerhub-user>/rag-chatbot:latest
```

## 4. Deploy App Container

Set environment variables in your cloud container service:

- `SUPABASE_DB_URL=postgresql+psycopg://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres?sslmode=require`
- `APP_HOST=0.0.0.0`
- `APP_PORT=8000`
- `OLLAMA_BASE_URL` (if Ollama reachable from your deployment network)
- `OLLAMA_EMBED_MODEL=bge-m3`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_STORAGE_BUCKET=documents`
- `SUPABASE_STORAGE_PREFIX=documents`
- `DOC_STORAGE_BACKEND` (optional, set to `supabase` or `local`)

Mount persistent storage for `/app/data` for chroma/secrets/settings.

After deploy, open `/settings` and save an OpenAI API key. Embeddings require this key for indexing and retrieval.

## 5. Run Health Check

- Open `/chat`
- Upload a file in `/data-management`
- Ask a question in `/chat`

## Single-Container Compose (Supabase)

Use `docker-compose.single.yml`:

```bash
docker compose -f docker-compose.single.yml up -d --build
```
