"""Sector risk scoring from inferred sector and dependencies."""

from __future__ import annotations

from typing import Any

from backend.app.services.risk.scoring_engine import clamp_score


SECTOR_TERMS = {
    "airlines": 60,
    "banks": 55,
    "real_estate": 55,
    "technology": 48,
    "unknown": 30,
}


def _sector_from_text(text: str) -> str:
    lowered = text.lower()
    for sector in ["airlines", "banks", "real_estate", "technology"]:
        if sector.replace("_", " ") in lowered or sector in lowered:
            return sector
    if "unknown" in lowered:
        return "unknown"
    return "unknown"


def score_sector_risk(reasoning_output: dict[str, Any]) -> dict[str, Any]:
    exposure = reasoning_output.get("financial_exposure_analysis") or {}
    text = exposure.get("sector_exposure", "")
    sector = _sector_from_text(text)
    evidence_map = reasoning_output.get("evidence_map") or []
    supported_sector_mentions = sum(1 for item in evidence_map if sector != "unknown" and sector.replace("_", " ") in str(item.get("evidence_text", "")).lower())
    score = clamp_score(SECTOR_TERMS.get(sector, 30) + min(supported_sector_mentions * 8, 20))
    limitation = "Sector is unknown; sector risk is generic and confidence should be reduced." if sector == "unknown" else ""
    return {
        "sector_risk_score": score,
        "sector": sector,
        "reason": limitation or f"Sector risk uses inferred sector {sector} and {supported_sector_mentions} supporting evidence mention(s).",
        "limitation": limitation,
    }
