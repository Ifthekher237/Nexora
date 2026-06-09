"""Editable sector dependency mappings for scenario reasoning."""

from __future__ import annotations

from typing import Any


SECTOR_DEPENDENCIES = {
    "airlines": [
        "fuel prices",
        "consumer demand",
        "travel restrictions",
        "aircraft maintenance",
        "labor cost",
    ],
    "banks": [
        "interest rates",
        "credit risk",
        "liquidity",
        "loan growth",
        "regulation",
    ],
    "real_estate": [
        "interest rates",
        "refinancing",
        "occupancy",
        "property valuations",
        "rental income",
    ],
    "technology": [
        "supply chain",
        "cloud spending",
        "semiconductor availability",
        "R&D investment",
    ],
    "unknown": [],
}


def infer_sector(company_name: str = "", ticker: str = "", evidence: list[dict[str, Any]] | None = None) -> str:
    haystack = " ".join(
        [
            company_name,
            ticker,
            " ".join(str(item.get("evidence_text") or item.get("chunk_text") or "") for item in evidence or []),
        ]
    ).lower()
    if any(term in haystack for term in ["qantas", "airline", "airways", "qan", "aviation"]):
        return "airlines"
    if any(term in haystack for term in ["bank", "loan", "deposit", "credit"]):
        return "banks"
    if any(term in haystack for term in ["real estate", "property", "reit"]):
        return "real_estate"
    if any(term in haystack for term in ["apple", "technology", "software", "semiconductor", "cloud", "aapl"]):
        return "technology"
    return "unknown"


def relevant_dependencies(sector: str, parsed_scenario: dict[str, Any]) -> dict[str, Any]:
    dependencies = SECTOR_DEPENDENCIES.get(sector, SECTOR_DEPENDENCIES["unknown"])
    scenario_terms = " ".join(
        [
            parsed_scenario.get("scenario_type", ""),
            parsed_scenario.get("macro_trigger", ""),
            parsed_scenario.get("sector_trigger", ""),
            " ".join(parsed_scenario.get("key_risk_keywords", [])),
        ]
    ).lower()
    relevant = [
        dependency
        for dependency in dependencies
        if any(part in scenario_terms for part in dependency.lower().split())
    ]
    return {
        "sector": sector,
        "dependencies": dependencies,
        "relevant_dependencies": relevant or dependencies[:2],
    }
