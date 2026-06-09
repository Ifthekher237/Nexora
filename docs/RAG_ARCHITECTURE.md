# Nexora RAG Architecture

Phase 5 adds a local-first retrieval-augmented generation pipeline on top of the
Phase 4 vector search layer.

## Core Flow

1. The user submits a financial question through Streamlit, the API, or
   `scripts/ask_rag.py`.
2. `rag_manager.py` validates the question, top_k, model, vector store, and
   metadata filters.
3. `query_understanding_service.py` classifies the question with simple
   rule-based logic and detects possible ticker/risk terms.
4. The manager calls the Phase 4 retrieval service to search FAISS or Chroma.
5. `context_builder.py` removes weak results below the configured score
   threshold and formats the remaining chunks as numbered evidence.
6. `prompt_builder.py` creates a financial RAG prompt that requires source
   citations, evidence-only answers, uncertainty, and no investment advice.
7. The manager calls Ollama locally through `ollama_service.py`.
8. `hallucination_guard.py` blocks no-evidence answers before the LLM and checks
   the final response for citations and stock-prediction language.
9. `citation_service.py` converts retrieved chunks into source objects with
   chunk IDs, document IDs, metadata, scores, and evidence text.
10. `confidence_service.py` estimates confidence from evidence count, retrieval
    scores, source diversity, and direct term overlap.
11. `rag_response_service.py` saves the full structured response and updates CSV
    and JSON history indexes.

## Evidence Context

Retrieved chunks are passed to the LLM in compact source blocks:

```text
[Source 1]
Score: 0.8200
Company: Apple Inc.
Ticker: AAPL
Document Type: SEC Filing Metadata
Published: 2026-05-29
Chunk ID: ...
Text:
...
```

The prompt instructs the model to cite these numbers exactly as `[Source 1]`.
Nexora does not fabricate citations; if no qualifying evidence exists, the LLM
is not called.

## Configuration

RAG settings live in `configs/rag_config.yaml`.

Important settings:

- `rag.min_retrieval_score`: filters weak evidence.
- `rag.max_top_k`: caps API and UI RAG requests.
- `rag.allow_answer_without_evidence`: defaults to false.
- `llm.default_model`: default Ollama model.
- `llm.temperature`, `llm.top_p`, `llm.max_tokens`: local generation controls.
- `retrieval.default_vector_store`: defaults to FAISS.

## API Endpoints

- `GET /rag/status`
- `POST /rag/ask`
- `POST /rag/evidence-only`
- `GET /rag/history`
- `GET /rag/history/{response_id}`

## Source Citations

Each source preserves:

- source number
- similarity score
- chunk ID
- source document ID
- processed document ID
- company name
- ticker
- market
- document type
- source type
- published date
- source URL when available
- evidence text

## Confidence

Confidence is not model self-reporting. It is computed from retrieval evidence:

- number of usable chunks
- average similarity score
- top similarity score
- number of unique source documents
- direct overlap with the question

Levels are `low`, `medium`, and `high`.

## Hallucination Guard

The guard enforces these rules:

- no evidence means no LLM call
- weak evidence produces an insufficient-evidence response
- missing citations trigger a source traceability appendix
- stock prediction or trading advice language triggers a limitation note

## Storage

Saved response bodies live under:

```text
data/rag_outputs/responses/
```

History indexes live at:

```text
data/rag_outputs/rag_response_index.csv
data/rag_outputs/rag_response_index.json
```

## Known Limitations

- Answer quality depends on retrieved evidence and local model quality.
- Nexora does not provide financial advice.
- Nexora does not predict stock prices.
- Phase 5 does not implement full scenario reasoning, risk scoring, or portfolio
  impact analysis.
- Query understanding is rule-based, not LLM-planned.

## Phase 6 Readiness

Phase 5 creates the evidence-grounded answer layer that Phase 6 can use as input
to a Financial Reasoning Engine. The next phase can build structured risk
extraction, scenario chains, and risk scoring on top of cited RAG evidence.
