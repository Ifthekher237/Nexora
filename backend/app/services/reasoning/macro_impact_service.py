"""Macro channel identification for financial reasoning."""

from __future__ import annotations

from typing import Any


MACRO_CHANNELS = [
    "inflation",
    "interest rates",
    "unemployment",
    "commodity prices",
    "exchange rates",
    "consumer demand",
    "liquidity",
    "regulation",
]


def identify_macro_channels(parsed_scenario: dict[str, Any], scenario_text: str = "") -> list[str]:
    scenario_type = parsed_scenario.get("scenario_type", "")
    text = f"{scenario_text} {scenario_type} {parsed_scenario.get('macro_trigger', '')}".lower()
    channels: list[str] = []
    if scenario_type == "oil_price_shock" or any(term in text for term in ["oil", "fuel", "commodity"]):
        channels.append("commodity prices")
    if "interest" in text or scenario_type == "interest_rate_change":
        channels.append("interest rates")
    if "inflation" in text:
        channels.append("inflation")
    if "currency" in text or "exchange" in text or "fx" in text:
        channels.append("exchange rates")
    if "demand" in text or "consumer" in text:
        channels.append("consumer demand")
    if "liquidity" in text or "cash" in text:
        channels.append("liquidity")
    if "regulation" in text or "regulatory" in text:
        channels.append("regulation")
    return [channel for channel in MACRO_CHANNELS if channel in channels]
