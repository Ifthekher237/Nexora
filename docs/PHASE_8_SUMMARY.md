# Phase 8 Summary: Explainability & Evidence Layer

Phase 8 adds a serious local-first explainability layer for Nexora. It audits
saved RAG, reasoning, and risk outputs and explains what evidence supports them,
which parts are uncertain, and where limitations remain.

## Implemented

- Explainability API routes under `backend/app/api/routes_explainability.py`
- Modular explainability services under `backend/app/services/explainability/`
- Pydantic schemas in `backend/app/schemas/explainability.py`
- YAML configuration in `configs/explainability_config.yaml`
- JSON/CSV report history under `data/explainability_outputs/`
- CLI scripts for explaining risk, reasoning, RAG, and latest outputs
- Streamlit `Explainability & Evidence` section
- Unit tests for citation expansion, evidence ranking, confidence explanation,
  limitation analysis, unsupported claim detection, and manager behavior

## What It Explains

For saved outputs, Phase 8 reports:

- explainability score
- evidence coverage level and reason
- expanded citations
- evidence ranking
- saved score or answer explanation
- confidence reasoning
- reasoning trace
- document attribution
- unsupported claim warnings
- limitations
- careful recommendation for use

## Evidence Rules

Phase 8 does not fake citations or invent missing source metadata. Missing fields
are marked `unknown`, and the report records a limitation.

Risk explanations use Phase 7 risk outputs and, when available, follow
`source_reasoning_id` back to Phase 6 evidence maps for citation expansion.

## How To Run

Backend:

```bash
./scripts/run_backend.sh
```

Frontend:

```bash
./scripts/run_frontend.sh
```

Explain latest risk output:

```bash
python3 scripts/explain_output.py --target-type risk --latest
```

Explain specific outputs:

```bash
python3 scripts/explain_risk.py --risk-id RISK_20260609_xxxxxx
python3 scripts/explain_reasoning.py --reasoning-id REASON_20260609_xxxxxx
python3 scripts/explain_output.py --target-type rag --target-id RAG_20260609_xxxxxx
```

View explainability history:

```bash
python3 scripts/show_explainability_history.py
```

Run tests:

```bash
python3 -m pytest
python3 scripts/test_explainability_pipeline.py
```

## Known Limitations

- Explainability depends on saved Phase 5, 6, and 7 outputs.
- Source quality depends on local ingestion, processing, retrieval, and metadata.
- Rule-based unsupported claim detection is conservative.
- This phase audits and explains outputs; it does not guarantee correctness.
- Nexora does not provide investment advice.
- Nexora does not predict stock prices.
- Full dashboard polish is deferred to Phase 9.

## Ready For Phase 9

Phase 9 can build the Streamlit Financial Intelligence Interface on top of the
saved explainability reports, evidence ranking, document attribution, and
confidence/limitation audit objects created here.
