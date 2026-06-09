# Phase 7 Summary: Risk Scoring Engine

Phase 7 adds transparent, deterministic risk scoring to Nexora. It scores
scenarios from Phase 6 reasoning outputs and available retrieval evidence,
producing a 0-100 risk estimate, risk level, confidence, score breakdown, risk
drivers, evidence summary, explanation, limitations, and saved history.

## Implemented

- `configs/risk_config.yaml`
- Risk API routes:
  - `GET /risk/status`
  - `POST /risk/score-scenario`
  - `POST /risk/score-from-reasoning/{reasoning_id}`
  - `GET /risk/history`
  - `GET /risk/history/{risk_id}`
  - `POST /risk/explain-score`
- Deterministic scoring services:
  - evidence strength
  - confidence
  - exposure
  - vulnerability
  - operational
  - macro
  - sector
  - company-specific
- Risk explanation and drivers
- Risk validation guardrails
- Risk output storage and history indexes
- Streamlit Risk Scoring Engine section
- CLI scripts
- Unit tests

## Score A Scenario

```bash
python3 scripts/score_risk.py \
  --scenario "What financial risks could appear if interest rates rise?" \
  --top-k 5
```

Company scenario:

```bash
python3 scripts/score_risk.py \
  --scenario "What happens to Qantas if oil prices rise by 25% over the next 6 months?" \
  --company-name "Qantas Airways" \
  --ticker QAN \
  --market ASX \
  --top-k 8
```

## Smoke Test

```bash
python3 scripts/run_risk_scoring.py
python3 scripts/test_risk_pipeline.py
```

## View History

```bash
python3 scripts/show_risk_history.py
```

## Testing

```bash
python3 -m pytest
python3 -c "from backend.app.main import app; print(app.title)"
```

## Limitations

- Scores depend on available evidence.
- Scores are analytical estimates, not predictions.
- No investment advice.
- No stock prediction.
- No final explainability dashboard yet.
- Local model quality affects upstream reasoning.

## Ready For Phase 8

Phase 7 prepares the Explainability & Evidence Layer by producing saved risk
scores with breakdowns, drivers, evidence summaries, confidence, and
limitations.
