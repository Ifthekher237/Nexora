"""Risk propagation agent."""

from __future__ import annotations

from typing import Any

from backend.app.services.agents.base_agent import BaseFinancialAgent
from backend.app.services.reasoning import causal_chain_service


class RiskPropagationAgent(BaseFinancialAgent):
    agent_key = "risk_propagation_agent"
    agent_name = "Risk Propagation Agent"
    description = "Reviews cause-effect paths, second-order impacts, and evidence-supported versus uncertain links."
    focus_terms = ["causal chain", "propagation", "downstream impact", "cash flow", "refinancing", "second order effects"]

    def run(self, context: dict[str, Any], memory: dict[str, Any]) -> dict[str, Any]:
        parsed = context.get("parsed_scenario", {})
        chain = causal_chain_service.build_causal_chain(parsed)
        evidence = self.retrieve_evidence(context)
        if evidence:
            for step in chain:
                step["evidence_strength"] = "contextual"
                step["supporting_sources"] = [item.get("source_number", "") for item in evidence[:2]]
                step["uncertainty"] = "Local evidence provides context, but the specific causal link still needs review."
        findings = [
            " -> ".join([str(step.get("cause")), str(step.get("effect"))])
            for step in chain
        ]
        if not evidence:
            summary = "A plausible propagation scaffold was produced, but no local evidence supported the links."
            status = "insufficient_evidence"
            limitations = [
                "Propagation path is a scenario scaffold when evidence is missing.",
                "Evidence-supported links could not be confirmed by local retrieval.",
                "Agent output is not financial advice and does not predict stock prices.",
            ]
        else:
            summary = "Risk propagation reviewed the scenario trigger and downstream causal path with local evidence context."
            status = "success"
            limitations = [
                "Causal links are evidence-informed but not mathematically proven.",
                "Second-order effects should be checked against additional company and sector evidence.",
                "Agent output is not financial advice and does not predict stock prices.",
            ]
        return {
            "agent_name": self.agent_name,
            "agent_key": self.agent_key,
            "status": status,
            "summary": summary,
            "key_findings": findings,
            "evidence_used": evidence,
            "confidence": self.confidence_from_evidence(
                evidence,
                "Causal scaffolds distinguish plausible links from evidence-supported links.",
            ),
            "limitations": limitations,
            "validation_warnings": [],
            "details": {"causal_chain": chain},
        }
