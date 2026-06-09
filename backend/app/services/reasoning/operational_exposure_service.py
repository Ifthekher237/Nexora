"""Operational exposure heuristics for scenario reasoning."""

from __future__ import annotations

from typing import Any


EXPOSURE_BY_SCENARIO = {
    "oil_price_shock": ["cost structure", "pricing power", "customer demand"],
    "interest_rate_change": ["debt/refinancing", "cash flow", "customer demand"],
    "inflation_pressure": ["cost structure", "labor", "pricing power", "customer demand"],
    "supply_chain_disruption": ["supply chain", "revenue sensitivity", "customer demand"],
    "revenue_pressure": ["revenue sensitivity", "cost structure", "cash flow"],
    "debt_refinancing_risk": ["debt/refinancing", "cash flow"],
    "liquidity_stress": ["cash flow", "cost structure", "customer demand"],
    "regulatory_change": ["regulatory compliance", "cost structure"],
    "consumer_demand_shift": ["customer demand", "revenue sensitivity", "pricing power"],
    "currency_movement": ["cost structure", "revenue sensitivity", "pricing power"],
    "unknown": ["cost structure", "revenue sensitivity"],
}


def identify_operational_exposures(
    parsed_scenario: dict[str, Any],
    evidence: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    scenario_type = parsed_scenario.get("scenario_type", "unknown")
    areas = list(EXPOSURE_BY_SCENARIO.get(scenario_type, EXPOSURE_BY_SCENARIO["unknown"]))
    evidence_text = " ".join(str(item.get("evidence_text") or "") for item in evidence or []).lower()

    if "debt" in evidence_text and "debt/refinancing" not in areas:
        areas.append("debt/refinancing")
    if "supply" in evidence_text and "supply chain" not in areas:
        areas.append("supply chain")
    if "labor" in evidence_text and "labor" not in areas:
        areas.append("labor")
    if "regulation" in evidence_text and "regulatory compliance" not in areas:
        areas.append("regulatory compliance")

    return {
        "areas": areas,
        "summary": "Potential operational exposure areas were inferred from the scenario type and retrieved evidence metadata/text; no precise exposure values are estimated in Phase 6.",
    }
