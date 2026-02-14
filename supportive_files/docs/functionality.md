# Functionality

## 1. Chat Interface (`/chat`)

- Streaming chat responses via NDJSON token stream.
- Retrieval-augmented generation (RAG) from Chroma vector database.
- LangChain-based model routing for providers:
  - `ollama` (default)
  - `openai`
  - `anthropic`
  - `gemini`
  - `groq`
- Embeddings and retrieval require an OpenAI API key saved in Settings.
- Graceful fallback responses when:
  - No files are indexed.
  - No relevant chunks are retrieved.
  - Provider/API key is missing.

## 2. Data Management (`/data-management`)

- Multi-file upload (`.pdf`, `.docx`, `.txt`).
- File parsing and text chunking.
- Vector indexing in Chroma (`documents` collection).
- File CRUD operations:
  - Create: upload and index.
  - Read: list indexed file metadata.
  - Update: replace file and re-index vectors.
  - Delete: remove both file and vectors.
- Edge-case handling:
  - Unsupported format
  - Empty file
  - Oversized file
  - Parse failure rollback
- Storage backend:
  - Supabase Storage when configured, otherwise local storage in `data/uploads/`.

## 3. Settings (`/settings`)

- Select active provider and model.
- Provider model discovery:
  - Ollama from `/api/tags` on the configured base URL
  - Groq from Groq models API when a Groq key is set (fallback catalog otherwise)
  - Other providers use a local catalog
- API key management for non-Ollama providers:
  - Single API key input for the currently selected provider
  - One provider key unlocks all models for that provider
  - Save/remove encrypted key
  - Status visibility (saved/missing)
- Persisted settings:
  - provider
  - model
  - ollama base URL
  - temperature
  - stored in `data/config/settings.json`

## 4. Security and Storage

- API keys encrypted at rest using Fernet.
- Encryption key stored in `data/secrets/fernet.key`.
- Metadata stored in PostgreSQL (documents).
- Uploaded files stored in Supabase Storage when configured; local fallback lives at `data/uploads/`.
- Chroma vectors stored in `data/chroma/`.
