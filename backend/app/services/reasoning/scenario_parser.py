"""Rule-based scenario parsing for financial reasoning."""

from __future__ import annotations

import re
from typing import Any


RISK_KEYWORDS = [
    "oil",
    "fuel",
    "interest rate",
    "inflation",
    "supply chain",
    "revenue",
    "debt",
    "liquidity",
    "regulation",
    "consumer demand",
    "currency",
]


def _scenario_type(text: str) -> str:
    lowered = text.lower()
    if any(term in lowered for term in ["oil", "fuel", "commodity price"]):
        return "oil_price_shock"
    if "interest rate" in lowered or "rates rise" in lowered or "rates increase" in lowered:
        return "interest_rate_change"
    if "inflation" in lowered:
        return "inflation_pressure"
    if any(term in lowered for term in ["supply chain", "shortage", "exports decline", "disruption"]):
        return "supply_chain_disruption"
    if "revenue" in lowered or "sales decline" in lowered:
        return "revenue_pressure"
    if "refinancing" in lowered or "borrowing" in lowered or "debt" in lowered:
        return "debt_refinancing_risk"
    if "liquidity" in lowered or "cash flow" in lowered:
        return "liquidity_stress"
    if "regulation" in lowered or "regulatory" in lowered or "compliance" in lowered:
        return "regulatory_change"
    if "consumer demand" in lowered or "demand shift" in lowered or "customers" in lowered:
        return "consumer_demand_shift"
    if "currency" in lowered or "exchange rate" in lowered or "fx" in lowered:
        return "currency_movement"
    return "unknown"


def _numerical_shock(text: str) -> str:
    percent_match = re.search(r"\b(?:by|of|rise|increase|decline|fall)?\s*(\d+(?:\.\d+)?)\s*%", text, re.I)
    if percent_match:
        return f"{percent_match.group(1)}%"
    basis_point_match = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:bps|basis points)\b", text, re.I)
    if basis_point_match:
        return f"{basis_point_match.group(1)} bps"
    return ""


def _time_horizon(text: str) -> str:
    match = re.search(
        r"\b(?:over|for|in|next)\s+(?:the\s+)?(\d+\s+(?:days?|weeks?|months?|quarters?|years?))\b",
        text,
        re.I,
    )
    return match.group(1) if match else ""


def _macro_trigger(scenario_type: str) -> str:
    return {
        "oil_price_shock": "commodity prices",
        "interest_rate_change": "interest rates",
        "inflation_pressure": "inflation",
        "currency_movement": "exchange rates",
        "liquidity_stress": "liquidity",
        "regulatory_change": "regulation",
        "consumer_demand_shift": "consumer demand",
    }.get(scenario_type, "")


def _sector_trigger(scenario_type: str) -> str:
    return {
        "oil_price_shock": "input cost exposure",
        "interest_rate_change": "financing sensitivity",
        "supply_chain_disruption": "supplier and input availability",
        "revenue_pressure": "sales and demand sensitivity",
        "debt_refinancing_risk": "debt maturity and borrowing exposure",
        "liquidity_stress": "cash and working-capital exposure",
        "regulatory_change": "compliance exposure",
        "consumer_demand_shift": "customer demand exposure",
        "currency_movement": "foreign exchange exposure",
    }.get(scenario_type, "")


def parse_scenario(
    scenario: str,
    company_name: str | None = None,
    ticker: str | None = None,
    market: str | None = None,
) -> dict[str, Any]:
    clean_scenario = " ".join(scenario.strip().split())
    scenario_type = _scenario_type(clean_scenario)
    lowered = clean_scenario.lower()

    return {
        "scenario_type": scenario_type,
        "company_name": (company_name or "").strip(),
        "ticker": (ticker or "").strip().upper(),
        "market": (market or "").strip().upper(),
        "macro_trigger": _macro_trigger(scenario_type),
        "sector_trigger": _sector_trigger(scenario_type),
        "key_risk_keywords": [keyword for keyword in RISK_KEYWORDS if keyword in lowered],
        "time_horizon": _time_horizon(clean_scenario),
        "numerical_shock": _numerical_shock(clean_scenario),
    }
