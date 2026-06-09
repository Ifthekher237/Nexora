# Nexora Risk Scoring Architecture

Phase 7 adds deterministic, evidence-backed risk scoring on top of Phase 6
reasoning, Phase 5 RAG evidence handling, and Phase 4 retrieval.

## Scoring Philosophy

Risk scores are 0-100 analytical estimates of scenario exposure and
vulnerability. They are not stock predictions, investment recommendations, or
financial advice.

Risk and confidence are separate:

- risk score estimates exposure/vulnerability
- confidence estimates how well available evidence supports that score

## Score Scale

- 0-20: very low
- 21-40: low
- 41-60: moderate
- 61-80: high
- 81-100: very high

## Core Flow

1. A scenario is submitted through Streamlit, API, or `scripts/score_risk.py`.
2. `risk_manager.py` calls Phase 6 reasoning or loads an existing reasoning
   output.
3. Evidence, causal chain, confidence, exposure analysis, and validation
   warnings are extracted from the reasoning output.
4. Component services calculate:
   - evidence strength
   - exposure breadth
   - vulnerability
   - operational risk
   - macro risk
   - sector risk
   - company-specific risk
   - confidence
5. `scoring_engine.py` combines configured weighted factors and maps the final
   score to a risk level.
6. `risk_validation_service.py` checks score bounds, confidence, evidence
   summary, limitations, advice language, stock prediction language, and
   unsupported certainty.
7. `risk_output_service.py` saves JSON output and CSV/JSON history indexes.

## Evidence Strength

Evidence strength uses:

- source count
- unique document count
- average retrieval score
- top retrieval score
- supported causal chain steps
- source diversity

Weak evidence reduces confidence and adds limitations.

## Exposure And Vulnerability

Exposure scoring looks for breadth across operational, macro, sector,
company-specific, causal-chain, and evidence-supported exposure areas.

Vulnerability scoring starts from scenario type and adds deterministic keyword
signals from reasoning/evidence text. It does not invent financial ratios or
historical metrics.

## Guardrails

Risk validation prevents:

- scores outside 0-100
- missing risk level
- missing confidence
- missing evidence summary
- missing limitations
- missing advice notice
- investment recommendation language
- stock prediction language
- unsupported certainty

## Storage

Saved risk outputs:

```text
data/risk_outputs/responses/
```

History indexes:

```text
data/risk_outputs/risk_index.csv
data/risk_outputs/risk_index.json
```

## Limitations

- Scores depend on available local evidence.
- No risk score is a prediction.
- No investment advice is provided.
- No stock price prediction is provided.
- No final explainability dashboard exists yet.
- Local LLM quality affects upstream Phase 6 reasoning.

## Phase 8 Readiness

Phase 7 outputs score breakdowns, evidence summaries, risk drivers, confidence,
limitations, and saved risk history. Phase 8 can use this as the foundation for
the Explainability & Evidence Layer.
