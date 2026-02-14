# RAG Chatbot

Production-structured, streaming RAG chatbot built with Python, HTML, CSS, and JavaScript.

## Project Layout

- `rag_core/` - RAG engine and storage modules (chunking, embeddings, retrieval, model routing).
- `app/api/` - FastAPI endpoints that call into `rag_core`.
- `app/templates` + `app/static` - HTML/CSS/JS UI.

## Core Stack

- FastAPI backend
- LangChain for chunking, retrieval, and multi-provider chat model integration
- PostgreSQL (Supabase) for document metadata
- JSON settings store for provider selection and API keys
- Supabase Storage for document files (local fallback)
- ChromaDB (persistent local) as vector DB
- `uv` for Python dependency and environment management

## Quick Start

Option A (uv):

```bash
uv sync
uv run python run.py
```

Option B (any venv):

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
python run.py
```

Open [http://localhost:8000](http://localhost:8000).

## Pages

- `/chat` - Streaming chatbot over indexed documents.
- `/data-management` - Upload, list, replace, and delete documents.
- `/settings` - Provider/model selection and API key management.

## Defaults

- Chat model (Ollama): `llama3.1:8b` for a strong quality/speed balance.
- Embeddings (Ollama): `bge-m3` for high-quality multilingual retrieval across providers.
- Embeddings are provider-agnostic, so you can switch chat models without re-indexing.
- If you change `OLLAMA_EMBED_MODEL`, re-upload documents to rebuild vectors.
- Embedding fallback order: Ollama → Gemini → OpenAI (if API keys exist).

## Documentation

- `supportive_files/docs/setup-and-run.md`
- `supportive_files/docs/functionality.md`
- `supportive_files/docs/tech-stack.md`
- `supportive_files/docs/deploy-single-container.md`
- `supportive_files/diagrams/architecture.puml`
- `supportive_files/diagrams/sequence-chat-streaming.puml`
