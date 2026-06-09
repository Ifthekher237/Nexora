# Nexora Explainability & Evidence Architecture

Phase 8 adds a local-first audit layer for saved Nexora outputs. It explains why
a RAG answer, reasoning chain, or risk score was produced by tracing it back to
saved citations, retrieval metadata, confidence signals, limitations, and
unsupported-claim warnings.

The layer does not generate investment advice, stock predictions, or new source
claims. It audits Phase 5, Phase 6, and Phase 7 outputs that already exist on
disk.

## Inputs

The explainability manager reads existing persisted outputs:

- Phase 5 RAG responses from `data/rag_outputs/responses/`
- Phase 6 reasoning responses from `data/reasoning_outputs/responses/`
- Phase 7 risk responses from `data/risk_outputs/responses/`
- Phase 4 vector metadata from `data/vector_store/metadata/vector_index.json`

Risk outputs do not store full citations directly. When a risk output includes a
`source_reasoning_id`, Phase 8 loads that reasoning output and uses its
`evidence_map` for source traceability.

## Services

`explainability_manager.py` coordinates the pipeline:

1. Load the target output.
2. Extract available source evidence.
3. Expand citations with real metadata.
4. Rank evidence using configured deterministic weights.
5. Extract reasoning trace and source support.
6. Attribute chunks to source documents.
7. Explain confidence separately from risk or severity.
8. Analyze limitations.
9. Detect unsupported claims using rule-based checks.
10. Validate and save the explainability report.

Supporting services:

- `citation_expander.py`: normalizes citation objects and fills missing fields as
  `unknown`.
- `evidence_ranker.py`: ranks evidence by retrieval score, source diversity,
  document relevance, citation usage, and recency.
- `evidence_coverage_service.py`: calculates low/medium/high evidence coverage.
- `reasoning_trace_service.py`: extracts causal-chain support and uncertainty.
- `document_attribution_service.py`: groups evidence by source document.
- `confidence_explainer.py`: explains confidence and separates it from risk.
- `limitation_analyzer.py`: extracts and adds cautious evidence limitations.
- `unsupported_claim_detector.py`: flags advice, stock prediction, certainty, and
  uncited financial claims.
- `explainability_validation_service.py`: applies report-level guardrails.
- `explainability_output_service.py`: saves reports and maintains history indexes.

## Citation Expansion

Citation expansion never invents attribution. It uses fields already present in
RAG `sources`, reasoning `evidence_map`, or Phase 4 vector metadata. Missing
fields are set to `unknown` and added to report limitations.

Expanded citation fields include chunk ID, source document ID, processed document
ID, company, ticker, market, document type, source type, published date,
retrieval score, source URL, citation usage, and a text excerpt.

## Evidence Ranking

Evidence ranking is deterministic and configured in
`configs/explainability_config.yaml`:

- retrieval score
- source diversity
- document relevance
- citation usage
- recency relative to available source dates

The ranking score is an audit signal, not a truth score.

## Confidence Explanation

Phase 8 preserves the saved output confidence and explains it using evidence
coverage, retrieval score, source count, limitations, validation warnings, and
unsupported-claim warnings.

The report explicitly distinguishes:

```text
High risk does not mean high confidence.
Low confidence does not mean low risk.
```

## Unsupported Claim Detection

Unsupported claim detection is rule-based. It checks generated text for:

- investment advice wording
- stock prediction wording
- guaranteed or certainty language
- financial claims without source references when citations are required

It does not use an LLM.

## Storage

Explainability reports are stored under:

```text
data/explainability_outputs/reports/
```

History indexes are stored at:

```text
data/explainability_outputs/explainability_index.csv
data/explainability_outputs/explainability_index.json
```

## API Endpoints

- `GET /explainability/status`
- `POST /explainability/explain-risk/{risk_id}`
- `POST /explainability/explain-reasoning/{reasoning_id}`
- `POST /explainability/explain-rag/{response_id}`
- `POST /explainability/explain-latest`
- `GET /explainability/history`
- `GET /explainability/history/{explainability_id}`

## Known Limitations

- Explainability depends on saved previous outputs.
- Source quality depends on ingestion, processing, and retrieval quality.
- Risk outputs need a readable `source_reasoning_id` for full citation expansion.
- Rule-based unsupported claim detection can produce conservative warnings.
- The layer audits saved outputs; it does not guarantee correctness.
- Nexora does not provide investment advice or stock price predictions.

## Phase 9 Readiness

Phase 8 creates report objects, history, evidence ranking, and attribution that a
future Streamlit Financial Intelligence Interface can display as a polished
end-to-end audit workflow.
