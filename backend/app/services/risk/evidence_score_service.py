"""Evidence strength scoring for risk outputs."""

from __future__ import annotations

from typing import Any

from backend.app.services.risk.scoring_engine import clamp_score


def evidence_summary(reasoning_output: dict[str, Any]) -> dict[str, Any]:
    evidence_map = reasoning_output.get("evidence_map") or []
    scores = [float(item.get("score") or 0.0) for item in evidence_map]
    unique_documents = {
        str(item.get("source_document_id", ""))
        for item in evidence_map
        if item.get("source_document_id")
    }
    chain = reasoning_output.get("causal_chain") or []
    supported_steps = sum(1 for step in chain if step.get("supporting_sources"))
    sources_used = len(evidence_map)
    return {
        "sources_used": sources_used,
        "unique_documents": len(unique_documents),
        "average_retrieval_score": round(sum(scores) / len(scores), 4) if scores else 0.0,
        "top_retrieval_score": round(max(scores), 4) if scores else 0.0,
        "supported_chain_steps": supported_steps,
        "source_diversity": round(len(unique_documents) / sources_used, 4) if sources_used else 0.0,
    }


def score_evidence_strength(reasoning_output: dict[str, Any]) -> dict[str, Any]:
    summary = evidence_summary(reasoning_output)
    sources_factor = min(summary["sources_used"] / 6, 1.0) * 25
    documents_factor = min(summary["unique_documents"] / 4, 1.0) * 20
    average_factor = min(summary["average_retrieval_score"], 1.0) * 25
    top_factor = min(summary["top_retrieval_score"], 1.0) * 15
    chain_factor = min(summary["supported_chain_steps"] / 4, 1.0) * 15
    score = clamp_score(sources_factor + documents_factor + average_factor + top_factor + chain_factor)
    if score >= 70:
        quality = "strong"
    elif score >= 40:
        quality = "moderate"
    else:
        quality = "weak"
    return {
        "evidence_strength_score": score,
        "evidence_quality_level": quality,
        "evidence_summary": summary,
        "reason": (
            f"Evidence score uses {summary['sources_used']} source(s), "
            f"{summary['unique_documents']} unique document(s), average score "
            f"{summary['average_retrieval_score']:.2f}, top score "
            f"{summary['top_retrieval_score']:.2f}, and {summary['supported_chain_steps']} "
            "supported chain step(s)."
        ),
    }
