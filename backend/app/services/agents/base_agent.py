"""Base utilities for simple local-first Nexora agents."""

from __future__ import annotations

from typing import Any

from backend.app.services.agents import agent_evidence_service


class BaseFinancialAgent:
    """Small base class shared by Phase 10 agents.

    This intentionally avoids an external agent framework. Each subclass defines
    role-specific focus terms and turns retrieved evidence into structured output.
    """

    agent_key = "base_agent"
    agent_name = "Base Agent"
    description = "Shared base class for Nexora agents."
    focus_terms: list[str] = []

    def evidence_query_terms(self, context: dict[str, Any]) -> list[str]:
        return self.focus_terms

    def retrieve_evidence(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        return agent_evidence_service.retrieve_agent_evidence(
            scenario=context["scenario"],
            focus_terms=self.evidence_query_terms(context),
            top_k=context["top_k"],
            vector_store=context.get("vector_store", "faiss"),
            filters=context.get("filters", {}),
            ticker=context.get("ticker", ""),
            market=context.get("market", ""),
        )

    def confidence_from_evidence(self, evidence: list[dict[str, Any]], extra_reason: str = "") -> dict[str, Any]:
        if not evidence:
            return {
                "level": "low",
                "score": 0.0,
                "reason": extra_reason or "No evidence was retrieved for this agent.",
            }
        scores = [float(item.get("score") or 0.0) for item in evidence]
        average = sum(scores) / len(scores)
        coverage_bonus = min(0.2, len(evidence) * 0.03)
        score = round(max(0.0, min(1.0, average + coverage_bonus)), 4)
        if score < 0.4:
            level = "low"
        elif score < 0.7:
            level = "medium"
        else:
            level = "high"
        reason = f"Based on {len(evidence)} evidence item(s) with average retrieval score {average:.2f}."
        if extra_reason:
            reason = f"{reason} {extra_reason}"
        return {"level": level, "score": score, "reason": reason}

    def no_evidence_output(self, summary: str, limitations: list[str] | None = None) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "agent_key": self.agent_key,
            "status": "insufficient_evidence",
            "summary": summary,
            "key_findings": [],
            "evidence_used": [],
            "confidence": self.confidence_from_evidence([]),
            "limitations": limitations
            or [
                "Not enough local evidence was available for this agent.",
                "Agent output is not financial advice and does not predict stock prices.",
            ],
            "validation_warnings": [],
            "details": {},
        }

    def findings_from_evidence(self, evidence: list[dict[str, Any]], prefix: str) -> list[str]:
        findings: list[str] = []
        for item in evidence[:3]:
            source = item.get("source_number", "Source")
            score = float(item.get("score") or 0.0)
            text = " ".join(str(item.get("evidence_text", "")).split())[:220]
            if text:
                findings.append(f"{prefix} {source} (score {score:.2f}) reports: {text}")
        return findings

    def run(self, context: dict[str, Any], memory: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
