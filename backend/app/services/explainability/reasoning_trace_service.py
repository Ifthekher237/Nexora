"""Extract a traceable reasoning path from saved RAG, reasoning, or risk outputs."""

from __future__ import annotations

from typing import Any


def extract_reasoning_trace(
    target_type: str,
    target_output: dict[str, Any],
    source_reasoning_output: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = source_reasoning_output or target_output
    causal_chain = source.get("causal_chain") if isinstance(source.get("causal_chain"), list) else []
    trace_steps: list[dict[str, Any]] = []
    supported_steps = 0
    uncertain_steps = 0
    for step in causal_chain:
        if not isinstance(step, dict):
            continue
        supporting_sources = step.get("supporting_sources") if isinstance(step.get("supporting_sources"), list) else []
        supported = bool(supporting_sources)
        supported_steps += 1 if supported else 0
        uncertain_steps += 0 if supported else 1
        trace_steps.append(
            {
                "step": step.get("step", len(trace_steps) + 1),
                "cause": step.get("cause", ""),
                "effect": step.get("effect", ""),
                "evidence_strength": step.get("evidence_strength", "unknown"),
                "supporting_sources": supporting_sources,
                "supported": supported,
                "uncertainty": step.get("uncertainty", ""),
            }
        )

    confidence = source.get("confidence") or target_output.get("confidence") or {}
    evidence_map = source.get("evidence_map") if isinstance(source.get("evidence_map"), list) else []
    if target_type == "rag":
        return {
            "target_type": target_type,
            "question": target_output.get("question", ""),
            "query_type": target_output.get("query_type", "unknown"),
            "causal_chain_steps": [],
            "supported_steps": 0,
            "uncertain_steps": 0,
            "evidence_items": len(target_output.get("sources") or []),
            "confidence_reason": confidence.get("reason", ""),
            "validation_warnings": [],
            "trace_note": "RAG answers do not include a causal chain; this trace audits source use and confidence only.",
        }

    return {
        "target_type": target_type,
        "scenario": source.get("scenario") or target_output.get("scenario", ""),
        "scenario_type": source.get("scenario_type") or target_output.get("scenario_type", "unknown"),
        "causal_chain_steps": trace_steps,
        "supported_steps": supported_steps,
        "uncertain_steps": uncertain_steps,
        "evidence_items": len(evidence_map),
        "confidence_reason": confidence.get("reason", ""),
        "validation_warnings": source.get("validation_warnings") or target_output.get("validation_warnings") or [],
        "trace_note": "Supported steps list explicit source references; uncertain steps had no supporting source in the saved output.",
    }
