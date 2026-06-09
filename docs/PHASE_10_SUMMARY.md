# Phase 10 Summary: AI Agent Collaboration System

Phase 10 implements Nexora's local-first AI Agent Collaboration System. It adds
specialized evidence-grounded agents, an orchestrator, shared run memory,
validation guardrails, saved run history, API endpoints, CLI scripts, tests, and
a Streamlit page.

## Implemented

- Agent configuration in `configs/agents_config.yaml`.
- Five specialized agents:
  - Macroeconomic Agent
  - Company Analysis Agent
  - Sector Analysis Agent
  - News Intelligence Agent
  - Risk Propagation Agent
- Sequential workflow orchestration with selected-agent support.
- Shared per-run memory for evidence, outputs, warnings, and intermediate
  findings.
- Local retrieval-backed evidence gathering through Phase 4 vector search.
- Scenario parsing and causal-chain reuse from Phase 6 reasoning services.
- Guardrails for investment-advice language, stock-prediction language, missing
  confidence, missing evidence references, and weak traceability.
- Collaboration summaries with agreements, uncertainties, evidence gaps, next
  steps, and overall confidence.
- Persistent agent run storage under `data/agent_outputs/`.
- FastAPI endpoints for status, available agents, workflow execution,
  single-agent execution, history list, and saved run detail.
- Streamlit AI Agent Collaboration page with workflow, single-agent, and history
  tabs.
- CLI scripts for running all agents, selected agents, history display, and a
  local smoke test.
- Backend unit tests for memory, validation, agents, orchestrator, and endpoint
  registration.

## How To Run Backend

```bash
./scripts/run_backend.sh
```

## How To Run Frontend

```bash
./scripts/run_frontend.sh
```

Open the Streamlit URL shown in the terminal, then select
`AI Agent Collaboration` from the sidebar.

## How To Run All Agents

```bash
python3 scripts/run_agents.py \
  --scenario "What financial risks could appear if interest rates rise?" \
  --top-k 5
```

## How To Run Selected Agents

```bash
python3 scripts/run_agent_workflow.py \
  --scenario "What financial risks could appear if interest rates rise?" \
  --agents macroeconomic_agent risk_propagation_agent \
  --top-k 5
```

## How To View Agent History

```bash
python3 scripts/show_agent_history.py
python3 scripts/show_agent_history.py --status success
python3 scripts/show_agent_history.py --agent-name macroeconomic_agent
```

## How To Test

```bash
python3 -m pytest
python3 scripts/test_agent_pipeline.py
python3 -c "from backend.app.main import app; print(app.title)"
```

## Known Limitations

- Output quality depends on already ingested, processed, and indexed local
  evidence.
- News analysis uses local RSS/news records only; it does not browse the live
  web.
- Company analysis requires a company name or ticker for company-specific
  conclusions.
- Sector inference is rule-based and should be reviewed when evidence is thin.
- Risk propagation is a causal scaffold unless local evidence supports specific
  links.
- The orchestrator runs agents sequentially in Phase 10.
- Nexora does not provide investment advice, trading recommendations, or stock
  price predictions.

## Ready For Phase 11

Phase 10 leaves Nexora ready for richer agent evaluation, report generation,
workflow comparison, deeper explainability integration, agent-specific prompt
templates, and optional UI polish without replacing the local-first pipeline.
