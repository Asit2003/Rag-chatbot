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
- Graceful fallback responses when:
  - No files are indexed.
  - No relevant chunks are retrieved.
  - Provider/API key is missing.

## 2. Data Management (`/data-management`)

- Multi-file upload (`.pdf`, `.docx`, `.txt`).
- File parsing and text chunking with LangChain splitter.
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

## 3. Settings (`/settings`)

- Select active provider and model.
- Ollama model discovery from `/api/tags`.
- Groq model discovery from Groq models API when Groq key is set, with fallback catalog.
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
- App metadata stored in PostgreSQL (Supabase).
- Uploaded files stored in Supabase Storage by default when configured.
- Local fallback storage lives at `data/uploads/`.
- Chroma vectors stored in `data/chroma/`.
