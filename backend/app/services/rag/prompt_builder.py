"""Prompt construction for evidence-grounded financial RAG answers."""

from __future__ import annotations

from typing import Any

from backend.app.core.config import get_rag_config


def build_prompt(
    question: str,
    evidence_context: str,
    query_understanding: dict[str, Any] | None = None,
) -> str:
    config = get_rag_config()
    prompt_config = config.get("prompting", {})
    system_role = prompt_config.get(
        "system_role",
        "You are Nexora, a financial evidence-grounded AI analyst assistant.",
    )
    answer_style = prompt_config.get("answer_style", "professional, concise, evidence-based")
    query_type = (query_understanding or {}).get("query_type", "unknown")
    risk_keywords = ", ".join((query_understanding or {}).get("risk_keywords", [])) or "none detected"

    return f"""System role:
{system_role}

Rules:
1. Use only the evidence provided.
2. Do not invent facts, numbers, companies, dates, or source details.
3. If evidence is insufficient, say so clearly.
4. Cite sources using [Source 1], [Source 2], and so on.
5. Do not give investment advice.
6. Do not predict exact stock prices or future market moves.
7. Focus on financial risk, exposure, and evidence.
8. Explain uncertainty and keep the answer {answer_style}.

Query understanding:
- Query type: {query_type}
- Risk keywords detected: {risk_keywords}

User question:
{question.strip()}

Retrieved evidence:
{evidence_context.strip()}

Required answer format:
- Direct Answer
- Evidence-Based Analysis
- Sources Used
- Confidence
- Limitations
"""
