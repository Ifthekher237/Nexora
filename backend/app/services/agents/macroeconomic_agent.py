"""Macroeconomic agent."""

from __future__ import annotations

from typing import Any

from backend.app.services.agents.base_agent import BaseFinancialAgent


class MacroeconomicAgent(BaseFinancialAgent):
    agent_key = "macroeconomic_agent"
    agent_name = "Macroeconomic Agent"
    description = "Reviews macroeconomic triggers such as interest rates, inflation, liquidity, commodities, and exchange rates."
    focus_terms = [
        "interest rates",
        "inflation",
        "unemployment",
        "commodity prices",
        "exchange rates",
        "liquidity",
        "central bank",
        "macro pressure",
    ]

    def evidence_query_terms(self, context: dict[str, Any]) -> list[str]:
        parsed = context.get("parsed_scenario", {})
        terms = list(self.focus_terms)
        if parsed.get("macro_trigger"):
            terms.insert(0, str(parsed["macro_trigger"]))
        return terms

    def run(self, context: dict[str, Any], memory: dict[str, Any]) -> dict[str, Any]:
        evidence = self.retrieve_evidence(context)
        if not evidence:
            return self.no_evidence_output(
                "Not enough local evidence was available to support a macroeconomic finding.",
                [
                    "No macro-relevant local retrieval evidence was found.",
                    "Macro agent does not browse the web or invent current macro facts.",
                    "Agent output is not financial advice and does not predict stock prices.",
                ],
            )
        findings = self.findings_from_evidence(evidence, "Macro evidence")
        summary = (
            "Macroeconomic review found local evidence relevant to scenario-level pressure. "
            "The strength of the finding depends on the cited retrieval evidence."
        )
        return {
            "agent_name": self.agent_name,
            "agent_key": self.agent_key,
            "status": "success",
            "summary": summary,
            "key_findings": findings,
            "evidence_used": evidence,
            "confidence": self.confidence_from_evidence(evidence),
            "limitations": [
                "Macro findings are limited to locally retrieved Nexora evidence.",
                "The agent does not browse for current central bank or market data.",
                "Agent output is not financial advice and does not predict stock prices.",
            ],
            "validation_warnings": [],
            "details": {"focus_terms": self.evidence_query_terms(context)},
        }
