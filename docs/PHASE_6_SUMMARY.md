# Phase 6 Summary: Financial Reasoning Engine

Phase 6 turns Nexora from evidence-grounded RAG answering into structured
scenario reasoning. It can parse financial scenarios, generate causal chain
scaffolds, retrieve evidence, map evidence to reasoning steps, ask a local
Ollama model for evidence-only reasoning, validate the output, and save
reasoning history.

## Implemented

- `configs/reasoning_config.yaml`
- Reasoning API routes:
  - `GET /reasoning/status`
  - `POST /reasoning/analyze-scenario`
  - `POST /reasoning/causal-chain`
  - `POST /reasoning/evidence-map`
  - `GET /reasoning/history`
  - `GET /reasoning/history/{reasoning_id}`
- Rule-based scenario parsing
- Causal chain templates
- Sector dependency mapping
- Macro channel detection
- Operational exposure detection
- Company mapping from local metadata only
- Evidence map generation from Phase 4 retrieval and Phase 5 RAG helpers
- Reasoning prompt builder
- Local Ollama multi-hop reasoning call
- Validation guardrails
- Reasoning output JSON/CSV history storage
- Streamlit Financial Reasoning Engine section
- CLI scripts and focused tests

## Analyze A Scenario

```bash
python3 scripts/analyze_scenario.py \
  --scenario "What happens to Qantas if oil prices rise by 25% over the next 6 months?" \
  --company-name "Qantas Airways" \
  --ticker QAN \
  --market ASX \
  --top-k 8
```

## Smoke Test

```bash
python3 scripts/run_reasoning.py
python3 scripts/test_reasoning_pipeline.py
```

## View History

```bash
python3 scripts/show_reasoning_history.py
```

Optional:

```bash
python3 scripts/show_reasoning_history.py --scenario-type interest_rate_change
python3 scripts/show_reasoning_history.py --status success
```

## Testing

```bash
python3 -m pytest
python3 -c "from backend.app.main import app; print(app.title)"
```

The unit tests do not require live Ollama.

## Limitations

- Reasoning depends on available retrieved evidence.
- No risk scoring yet.
- No final enterprise dashboard yet.
- Not financial advice.
- No stock prediction.
- Local LLM quality depends on selected Ollama model.

## Ready For Phase 7

Phase 6 outputs structured causal chains, exposure analysis, evidence maps,
confidence, and validation warnings. Phase 7 can use these records to implement
the Risk Scoring Engine.
