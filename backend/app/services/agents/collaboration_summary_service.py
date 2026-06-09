"""Generate transparent collaboration summaries from agent outputs."""

from __future__ import annotations

from typing import Any


def overall_confidence(agent_outputs: list[dict[str, Any]]) -> dict[str, Any]:
    scores = [
        float((output.get("confidence") or {}).get("score") or 0.0)
        for output in agent_outputs
        if output.get("status") in {"success", "insufficient_evidence"}
    ]
    score = round(sum(scores) / len(scores), 4) if scores else 0.0
    if score < 0.4:
        level = "low"
    elif score < 0.7:
        level = "medium"
    else:
        level = "high"
    return {
        "level": level,
        "score": score,
        "reason": f"Average confidence across {len(scores)} completed agent output(s).",
    }


def build_summary(agent_outputs: list[dict[str, Any]], scenario: str) -> dict[str, Any]:
    completed = [output for output in agent_outputs if output.get("status") == "success"]
    weak = [output for output in agent_outputs if output.get("status") != "success"]
    key_agreements: list[str] = []
    key_uncertainties: list[str] = []
    evidence_gaps: list[str] = []

    for output in completed:
        findings = output.get("key_findings") or []
        if findings:
            key_agreements.append(f"{output.get('agent_name')}: {findings[0]}")
    for output in agent_outputs:
        confidence = output.get("confidence") or {}
        if output.get("status") != "success" or confidence.get("level") == "low":
            key_uncertainties.append(
                f"{output.get('agent_name')}: {confidence.get('reason', 'Low or incomplete evidence support.')}"
            )
        for limitation in output.get("limitations", []):
            lowered = str(limitation).lower()
            if any(term in lowered for term in ["limited", "missing", "no ", "weak", "not enough"]):
                if limitation not in evidence_gaps:
                    evidence_gaps.append(str(limitation))

    next_steps = [
        "Review the cited chunks before relying on the collaboration summary.",
        "Run explainability on any saved risk or reasoning output used for decisions.",
    ]
    if evidence_gaps:
        next_steps.insert(0, "Add or ingest more targeted evidence before making stronger conclusions.")
    if any("company" in gap.lower() for gap in evidence_gaps):
        next_steps.append("Ingest company-specific reports or filings before relying on company-level conclusions.")

    combined_view = (
        f"{len(completed)} agent(s) produced evidence-grounded outputs for the scenario. "
        f"{len(weak)} agent(s) reported weak, missing, or failed evidence. "
        "The summary is analytical and not a recommendation to trade."
    )
    if not completed:
        combined_view = (
            "No agent produced a strong evidence-grounded output. More local evidence is needed before drawing conclusions."
        )
    return {
        "combined_view": combined_view,
        "key_agreements": key_agreements[:8],
        "key_uncertainties": key_uncertainties[:8],
        "evidence_gaps": evidence_gaps[:10],
        "recommended_next_steps": next_steps[:6],
    }
