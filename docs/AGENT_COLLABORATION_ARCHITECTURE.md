# Nexora Agent Collaboration Architecture

Phase 10 adds a local-first AI Agent Collaboration System on top of Nexora's
existing retrieval, RAG, reasoning, risk, and explainability foundations.

The system is intentionally not an external agent framework. Agents are small
specialized services that retrieve local evidence, produce structured outputs,
share workflow memory, pass validation guardrails, and save auditable run
history.

## Components

- `configs/agents_config.yaml`: enabled agents, top-k limits, model defaults,
  persistence paths, workflow flags, and guardrails.
- `backend/app/api/routes_agents.py`: FastAPI routes for status, available
  agents, workflow execution, single-agent execution, and saved history.
- `backend/app/schemas/agents.py`: Pydantic contracts for requests, agent
  outputs, confidence, evidence, collaboration summaries, and history rows.
- `backend/app/services/agents/base_agent.py`: shared retrieval, confidence,
  no-evidence, and finding helpers.
- `backend/app/services/agents/agent_orchestrator.py`: sequential workflow
  orchestration, shared memory, per-agent validation, collaboration summary, and
  output persistence.
- `backend/app/services/agents/agent_memory_service.py`: per-run shared memory
  for evidence, outputs, intermediate findings, and warnings.
- `backend/app/services/agents/agent_evidence_service.py`: adapter from agent
  focus terms to Phase 4 vector retrieval results.
- `backend/app/services/agents/agent_validation_service.py`: guardrails against
  investment-advice language, stock predictions, unsupported success outputs,
  missing confidence, and weak source traceability.
- `backend/app/services/agents/agent_output_service.py`: saved JSON responses
  and CSV/JSON history indexes.
- `backend/app/services/agents/collaboration_summary_service.py`: combined view,
  agreements, uncertainties, evidence gaps, next steps, and overall confidence.
- `frontend/app_pages/agents_page.py`: Streamlit workflow, single-agent, and
  history UI.

## Agents

- Macroeconomic Agent: reviews locally retrieved evidence for interest rates,
  inflation, unemployment, commodities, exchange rates, liquidity, and central
  bank pressure.
- Company Analysis Agent: reviews company/ticker-specific evidence, including
  filings, revenue, cost, debt, liquidity, and cash-flow mentions.
- Sector Analysis Agent: infers sector context from company/ticker/evidence and
  applies existing sector dependency mappings.
- News Intelligence Agent: uses only locally ingested RSS/news evidence. It does
  not browse the web for current events.
- Risk Propagation Agent: builds a local causal-chain scaffold and marks links
  as evidence-contextual only when local retrieval evidence exists.

## Workflow

1. The API validates the request and selected agents.
2. The orchestrator parses the scenario with the existing Phase 6 parser.
3. A shared per-run memory object is created.
4. Agents run sequentially, using local retrieval/RAG-era evidence interfaces.
5. Each agent output is validated by guardrails.
6. Outputs are stored in shared memory.
7. A collaboration summary and overall confidence are generated.
8. The response is saved under `data/agent_outputs/runs/`.
9. CSV and JSON indexes are updated for history views.

## API Endpoints

- `GET /agents/status`
- `GET /agents/available`
- `POST /agents/run-workflow`
- `POST /agents/run-single`
- `GET /agents/history`
- `GET /agents/history/{agent_run_id}`

## Storage

Saved response bodies are stored under:

```text
data/agent_outputs/runs/
```

History indexes are stored at:

```text
data/agent_outputs/agent_run_index.csv
data/agent_outputs/agent_run_index.json
```

Run bodies are ignored by git, while the empty storage directory and history
index files remain part of the local project structure.

## Guardrails

The system does not:

- provide investment advice
- issue buy, sell, or hold recommendations
- predict stock prices
- browse the web for live news
- invent evidence or fake agent outputs
- claim certainty when local evidence is missing

When evidence is missing, agents return `insufficient_evidence` with low
confidence and explicit limitations.

## Phase 11 Readiness

Phase 10 creates a stable orchestration layer that Phase 11 can extend into
report generation, comparison workflows, deeper explainability reports, richer
frontend visualizations, and more robust workflow-level evaluation.
