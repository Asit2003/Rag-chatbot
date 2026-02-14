# Tech Stack and Why

## Backend

- **FastAPI**: async-friendly API framework with clean route/dependency model.
- **SQLAlchemy + PostgreSQL (Supabase)**: document metadata persistence (Supabase-only).
- **Supabase Storage**: document file storage when configured (local storage fallback).
- **LangChain**:
  - `RecursiveCharacterTextSplitter` for consistent chunking.
  - LangChain chat model integrations for OpenAI, Anthropic, Gemini, Groq, and Ollama.
  - `langchain-chroma` integration for retrieval from vector DB.
- **ChromaDB (persistent)**: free/open-source vector database for local or containerized deployment.
- **Embeddings**: OpenAI embeddings (API key required for indexing and retrieval).
- **PyPDF + python-docx**: extraction for PDF and DOCX.
- **JSON settings + Cryptography (Fernet)**: encrypted API-key storage at rest in `data/config/settings.json`.
- **uv**: fast dependency and virtual environment management.

## Frontend

- **HTML templates (Jinja)**: simple server-rendered architecture.
- **Vanilla JavaScript**: precise handling for streaming and CRUD actions.
- **Custom CSS**: clean, responsive, professional UI.

## Why This Is a Strong Fit

- Meets requested stack: Python + HTML/CSS/JS with LangChain and PostgreSQL.
- Keeps provider flexibility while defaulting to local Ollama.
- Clear production-oriented layering:
  - API routes
  - services
  - repositories
  - schemas
  - templates/static assets
- Supports cloud deployment with single-container or multi-container topology.
