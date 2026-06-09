# Nexora Architecture

Nexora Phase 1 is a local-first infrastructure foundation for a future financial
scenario intelligence system.

## Backend Architecture

The backend is a modular FastAPI application under `backend/app/`.

- `main.py` initializes the FastAPI app, registers routers, and logs startup.
- `api/` contains route modules grouped by purpose.
- `core/` contains configuration, logging, and system health helpers.
- `services/` contains runtime-facing business logic.
- `schemas/` contains Pydantic request and response models.

This keeps HTTP concerns separate from configuration, runtime integration, and
future reasoning services.

## Frontend Architecture

The Streamlit frontend lives under `frontend/`.

- `streamlit_app.py` provides the Phase 1 operational interface.
- `ui_helpers.py` centralizes backend and Ollama HTTP calls.

The UI checks backend status, reads model configuration, checks Ollama
connectivity, and sends a local inference test through FastAPI.

## Configuration System

Configuration is stored in YAML files under `configs/`.

- `app_config.yaml` defines local app, backend, frontend, and logging settings.
- `model_config.yaml` defines the primary runtime, llama.cpp-ready secondary
  runtime, default model, and available local models.

`backend/app/core/config.py` loads these files and applies small `.env` overrides
for local machine differences.

## Logging System

`backend/app/core/logging_config.py` configures readable console logging and
optional file logging to `logs/nexora.log`.

Important events logged in Phase 1 include:

- app startup
- logging setup
- model registry loading
- inference requests
- Ollama connection success or failure

## Model Runtime Layer

The model runtime layer starts with Ollama and is structured for future llama.cpp
support.

- `model_registry.py` validates model names against `configs/model_config.yaml`.
- `ollama_service.py` checks the local Ollama API and calls `/api/generate`.
- `inference_service.py` coordinates validation and local runtime calls.

The backend does not call any paid API or cloud inference provider.

## Ollama Integration

Ollama is accessed through its local HTTP API at `http://localhost:11434`.

The integration handles:

- server reachability checks
- local model generation requests
- connection errors
- timeouts
- missing or mismatched local model tags

When Ollama is not running, the API returns a clean error instead of crashing.

## Future Expansion Points

Phase 2 and later phases can extend the current architecture without replacing
the foundation.

### Ingestion

Add source-specific ingestion services under `backend/app/services/` and expose
controlled ingestion routes under `backend/app/api/`.

### Document Processing

Add parsers for PDFs, web pages, spreadsheets, and financial text. PyPDF,
BeautifulSoup, and Pandas can be introduced when those workflows are implemented.

### Vector Database

Add vector storage adapters for FAISS or ChromaDB in a dedicated service module.
Keep vector database configuration in `configs/`.

### RAG

Add retrieval orchestration in a separate service that combines documents,
embedding search, and local model calls. LangChain or LlamaIndex can be added
only when RAG is actually implemented.

### Reasoning Engine

Build financial scenario reasoning as its own backend service. It should consume
validated data and retrieved context rather than living inside the route layer.

### Risk Scoring

Add explicit scoring schemas, explainable scoring functions, and test coverage.
Risk scoring should remain separate from raw model output.

### Explainability

Add structured explanation outputs that cite source data and intermediate
reasoning artifacts. This is a later-phase requirement, not Phase 1 behavior.
