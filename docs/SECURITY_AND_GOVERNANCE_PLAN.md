# Nexora Security And Governance Plan

Nexora remains local-first. Phase 12 documents practical security and governance
requirements for future enterprise deployment.

## Current Security Position

- Local-first by default.
- No production authentication is implemented yet.
- No production authorization is implemented yet.
- No enterprise secrets manager is configured.
- `.env` is ignored by git and should remain local.
- No paid APIs or OpenAI API are required.

## Future Authentication Plan

- Integrate with an organization identity provider.
- Protect FastAPI routes before shared deployment.
- Keep local developer mode separate from production mode.

## Future Authorization Plan

Suggested roles:

- admin
- analyst
- auditor
- read-only reviewer

Sensitive actions such as ingestion, deletion, report generation, and benchmark
execution should be role-restricted before enterprise deployment.

## Data Governance Plan

- Raw data lives under `data/raw/`.
- Processed text and chunks live under `data/processed/`.
- Vector metadata lives under `data/vector_store/metadata/`.
- RAG, reasoning, risk, explainability, agent, performance, and deployment
  outputs live in phase-specific `data/*_outputs/` folders.

## Retention And Deletion

Future enterprise use should define:

- retention windows for raw and processed data
- deletion workflows that remove raw, processed, vector, and output references
- audit records for deletion actions
- review of source licensing and privacy requirements

## Limitations

This plan is not a security certification. Enterprise use requires formal
security review, data governance approval, and legal/source licensing review.
