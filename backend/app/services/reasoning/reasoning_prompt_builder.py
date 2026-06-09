"""Prompt builder for local financial scenario reasoning."""

from __future__ import annotations

from typing import Any


def _format_chain(chain_steps: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"{step['step']}. {step['cause']} -> {step['effect']} "
        f"(current evidence strength: {step.get('evidence_strength', 'low')})"
        for step in chain_steps
    )


def build_reasoning_prompt(
    scenario: str,
    parsed_scenario: dict[str, Any],
    causal_chain: list[dict[str, Any]],
    evidence_context: str,
    company_map: dict[str, Any],
    sector_dependencies: dict[str, Any],
    macro_channels: list[str],
    operational_exposures: dict[str, Any],
) -> str:
    return f"""System role:
You are Nexora, a financial scenario reasoning assistant.

Rules:
1. Use only provided evidence.
2. Do not make unsupported claims.
3. Separate evidence-supported findings from plausible assumptions.
4. Do not give investment advice.
5. Do not predict exact stock prices.
6. Cite source numbers.
7. Explain uncertainty clearly.

Scenario:
{scenario}

Parsed scenario:
{parsed_scenario}

Company mapping:
{company_map}

Sector dependencies:
{sector_dependencies}

Macro channels:
{macro_channels}

Operational exposure areas:
{operational_exposures}

Causal chain scaffold:
{_format_chain(causal_chain)}

Retrieved evidence:
{evidence_context}

Required output:
- Direct Answer
- Causal Chain
- Financial Exposure Analysis
- Evidence Map
- Confidence
- Limitations
"""
