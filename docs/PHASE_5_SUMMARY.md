# Phase 5 Summary: Core Financial RAG Pipeline

Phase 5 adds a serious local-first RAG layer to Nexora. The system can now take
a financial question, retrieve local evidence from the Phase 4 vector index,
build a grounded prompt, call a local Ollama model, return source-attributed
answers, estimate confidence, and save response history.

## Implemented

- RAG config in `configs/rag_config.yaml`
- RAG FastAPI routes:
  - `GET /rag/status`
  - `POST /rag/ask`
  - `POST /rag/evidence-only`
  - `GET /rag/history`
  - `GET /rag/history/{response_id}`
- Central RAG manager under `backend/app/services/rag/rag_manager.py`
- Rule-based query understanding
- Evidence context builder with score filtering
- Financial RAG prompt builder
- Citation/source object generation
- Retrieval-quality confidence scoring
- Hallucination guard for no-evidence, missing-citation, and stock-prediction
  cases
- JSON response saving plus CSV/JSON history indexes
- Streamlit `Financial RAG Assistant` section
- CLI scripts for asking RAG, testing the pipeline, and viewing history
- Unit tests for the new RAG services

## How To Ask A Question

```bash
python3 scripts/ask_rag.py \
  --question "What financial risks are mentioned in the available documents?" \
  --top-k 5
```

Optional filters:

```bash
python3 scripts/ask_rag.py \
  --question "What risks relate to interest rates?" \
  --ticker AAPL \
  --top-k 5
```

## Evidence-Only Debugging

Use the API:

```text
POST /rag/evidence-only
```

Example body:

```json
{
  "question": "What financial risks are mentioned in the available documents?",
  "top_k": 5,
  "vector_store": "faiss",
  "filters": {
    "ticker": null,
    "source_type": null,
    "document_type": null,
    "market": null,
    "section_hint": null
  }
}
```

## View History

```bash
python3 scripts/show_rag_history.py
```

Optional filters:

```bash
python3 scripts/show_rag_history.py --ticker AAPL
python3 scripts/show_rag_history.py --status success
python3 scripts/show_rag_history.py --confidence-level medium
```

## Testing

```bash
python3 -m pytest
python3 -c "from backend.app.main import app; print(app.title)"
python3 scripts/test_rag_pipeline.py
```

The unit tests do not require Ollama. The smoke script reports clearly if
retrieval works but Ollama is not running.

## Limitations

- RAG answers are limited to retrieved local evidence.
- Local model quality depends on the selected Ollama model.
- The system does not provide investment advice.
- The system does not predict stock prices.
- Phase 5 does not include full risk scoring, scenario reasoning, or portfolio
  impact modelling.

## Ready For Phase 6

Phase 5 produces structured, cited, confidence-scored answers and saved RAG
records. Phase 6 can use those outputs to build a Financial Reasoning Engine
with risk extraction, scenario relationships, and deeper financial analysis.
