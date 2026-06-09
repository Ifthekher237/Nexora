# Nexora Reasoning Architecture

Phase 6 adds the Financial Reasoning Engine on top of Phase 4 retrieval and
Phase 5 RAG evidence handling. It interprets a scenario, creates a causal
scaffold, retrieves supporting evidence, asks a local Ollama model to reason
from that evidence, validates the output, and saves a structured reasoning
record.

## Core Flow

1. A user submits a scenario through Streamlit, the API, or
   `scripts/analyze_scenario.py`.
2. `scenario_parser.py` detects scenario type, ticker, market, time horizon,
   numerical shock, macro trigger, sector trigger, and risk keywords.
3. `causal_chain_service.py` creates a scenario-specific causal scaffold.
4. `reasoning_evidence_service.py` searches the Phase 4 vector index and uses
   Phase 5 context/citation helpers to build evidence maps.
5. Sector, macro, operational, and company mapping services add rule-based
   context without inventing a company database.
6. `reasoning_prompt_builder.py` builds a strict evidence-only local prompt.
7. `multi_hop_reasoning_service.py` calls Ollama through the existing local
   Ollama service.
8. `reasoning_validation_service.py` checks citations, advice language, stock
   prediction language, causal chain presence, limitations, and weak-evidence
   certainty.
9. `reasoning_output_service.py` saves the full JSON output and updates CSV/JSON
   history indexes.

## Scenario Parsing

The parser is rule-based. Examples:

- `oil prices rise by 25%` becomes `oil_price_shock` with `25%`.
- `interest rates increase by 1%` becomes `interest_rate_change` with `1%`.
- `exports decline` or `supply chain disruption` becomes
  `supply_chain_disruption`.

No LLM planning is required for Phase 6 parsing.

## Causal Chains

Causal chains are scaffolds, not final claims. Each step starts as low evidence
strength and is then checked against retrieved evidence.

Example oil-price scaffold:

```text
Oil price increase
-> Higher input or fuel cost exposure
-> Operating margin pressure
-> Possible pricing or cost-control response
-> Demand sensitivity risk
-> Revenue and margin uncertainty
```

Unsupported steps remain marked as uncertain.

## Evidence Retrieval

Reasoning evidence retrieval uses:

- Phase 4 retrieval service
- FAISS by default
- Phase 5 context builder
- Phase 5 citation/source conversion
- metadata filters for ticker, market, source type, document type, and section
  hint

The evidence map preserves source numbers, scores, chunk IDs, document IDs,
relevance, and how the evidence is used in the reasoning chain.

## Prompting

The reasoning prompt instructs the model to:

- use only provided evidence
- separate evidence-supported findings from plausible assumptions
- cite source numbers
- avoid investment advice
- avoid stock price prediction
- explain uncertainty

## Validation

Validation lowers confidence and adds warnings when it detects:

- missing citations
- missing causal chain
- missing evidence map
- missing limitations
- investment advice language
- stock prediction language
- certainty language with weak confidence

## Storage

Saved reasoning outputs live under:

```text
data/reasoning_outputs/responses/
```

History indexes:

```text
data/reasoning_outputs/reasoning_index.csv
data/reasoning_outputs/reasoning_index.json
```

## Limitations

- Reasoning depends on retrieved local evidence.
- Phase 6 does not calculate final risk scores.
- Phase 6 does not build the enterprise dashboard.
- Nexora does not provide financial advice.
- Nexora does not predict stock prices.
- Local LLM quality depends on the installed Ollama model.

## Phase 7 Readiness

Phase 6 produces structured scenario type, causal chain, exposure analysis,
evidence map, confidence, warnings, and limitations. Phase 7 can use those
outputs as the input layer for a Risk Scoring Engine.
