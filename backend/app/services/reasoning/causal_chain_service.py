"""Causal-chain scaffolds for financial scenario reasoning."""

from __future__ import annotations

from typing import Any


CHAIN_TEMPLATES: dict[str, list[tuple[str, str]]] = {
    "oil_price_shock": [
        ("Oil price increase", "Higher input or fuel cost exposure"),
        ("Higher fuel or input costs", "Operating margin pressure"),
        ("Margin pressure", "Possible pricing or cost-control response"),
        ("Pricing response", "Demand sensitivity risk"),
        ("Demand sensitivity", "Revenue and margin uncertainty"),
    ],
    "interest_rate_change": [
        ("Interest rate increase", "Borrowing cost increase"),
        ("Borrowing cost increase", "Refinancing pressure"),
        ("Refinancing pressure", "Cash flow pressure"),
        ("Cash flow pressure", "Expansion or investment constraint"),
    ],
    "inflation_pressure": [
        ("Inflation pressure", "Input and labor cost pressure"),
        ("Cost pressure", "Pricing power test"),
        ("Pricing response", "Consumer demand sensitivity"),
        ("Demand sensitivity", "Revenue and margin uncertainty"),
    ],
    "supply_chain_disruption": [
        ("Supply disruption", "Input shortage"),
        ("Input shortage", "Production or service delay"),
        ("Operational delay", "Revenue timing pressure"),
        ("Customer impact", "Demand or reputation uncertainty"),
    ],
    "revenue_pressure": [
        ("Revenue pressure", "Lower sales or weaker pricing"),
        ("Lower sales", "Operating leverage pressure"),
        ("Margin pressure", "Cash flow uncertainty"),
    ],
    "debt_refinancing_risk": [
        ("Debt refinancing risk", "Higher borrowing or rollover cost"),
        ("Rollover cost pressure", "Cash flow pressure"),
        ("Cash flow pressure", "Capital allocation constraint"),
    ],
    "liquidity_stress": [
        ("Liquidity stress", "Working-capital constraint"),
        ("Working-capital constraint", "Operational flexibility pressure"),
        ("Operational pressure", "Financial resilience uncertainty"),
    ],
    "regulatory_change": [
        ("Regulatory change", "Compliance requirement shift"),
        ("Compliance requirement", "Cost or operational change"),
        ("Operational change", "Revenue or margin uncertainty"),
    ],
    "consumer_demand_shift": [
        ("Consumer demand shift", "Volume or pricing pressure"),
        ("Volume pressure", "Revenue sensitivity"),
        ("Revenue sensitivity", "Margin and cash flow uncertainty"),
    ],
    "currency_movement": [
        ("Currency movement", "Import, export, or translation exposure"),
        ("FX exposure", "Revenue or cost volatility"),
        ("Volatility", "Margin uncertainty"),
    ],
    "unknown": [
        ("Scenario trigger", "Potential financial exposure"),
        ("Exposure", "Operational or financial uncertainty"),
    ],
}


def build_causal_chain(parsed_scenario: dict[str, Any]) -> list[dict[str, Any]]:
    scenario_type = parsed_scenario.get("scenario_type", "unknown")
    template = CHAIN_TEMPLATES.get(scenario_type, CHAIN_TEMPLATES["unknown"])
    return [
        {
            "step": index,
            "cause": cause,
            "effect": effect,
            "evidence_strength": "low",
            "supporting_sources": [],
            "uncertainty": "This is a scenario scaffold and must be checked against retrieved evidence.",
        }
        for index, (cause, effect) in enumerate(template, start=1)
    ]
