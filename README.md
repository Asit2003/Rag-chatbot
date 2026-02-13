# RAG Chatbot

Production-structured, streaming RAG chatbot built with Python, HTML, CSS, and JavaScript.

## Core Stack

- FastAPI backend
- LangChain for chunking, retrieval, and multi-provider chat model integration
- PostgreSQL (Supabase connection URL supported directly) for app metadata/settings storage
- ChromaDB (persistent local) as vector DB
- `uv` for Python dependency and environment management

## Quick Start (uv)

```bash
export UV_PROJECT_ENVIRONMENT=rag
uv sync
uv run python run.py
```

Open [http://localhost:8000](http://localhost:8000).

## Pages

- `/chat` - Streaming chatbot over indexed documents.
- `/data-management` - Upload, list, replace, and delete documents.
- `/settings` - Provider/model selection and API key management.

## Documentation

- `docs/setup-and-run.md`
- `docs/functionality.md`
- `docs/tech-stack.md`
- `docs/deploy-single-container.md`
- `docs/deploy-separate-containers.md`
- `diagrams/architecture.puml`
- `diagrams/sequence-chat-streaming.puml`
