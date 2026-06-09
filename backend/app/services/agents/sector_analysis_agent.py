"""Sector analysis agent."""

from __future__ import annotations

from typing import Any

from backend.app.services.agents.base_agent import BaseFinancialAgent
from backend.app.services.reasoning import sector_dependency_service


class SectorAnalysisAgent(BaseFinancialAgent):
    agent_key = "sector_analysis_agent"
    agent_name = "Sector Analysis Agent"
    description = "Reviews sector dependencies, scenario-sector fit, and industry-level exposure."
    focus_terms = ["sector", "industry", "dependency", "demand", "input costs", "financing sensitivity", "supply"]

    def evidence_query_terms(self, context: dict[str, Any]) -> list[str]:
        parsed = context.get("parsed_scenario", {})
        sector_info = sector_dependency_service.relevant_dependencies(
            context.get("sector", "unknown"),
            parsed,
        )
        return list(self.focus_terms) + sector_info.get("relevant_dependencies", [])

    def run(self, context: dict[str, Any], memory: dict[str, Any]) -> dict[str, Any]:
        evidence = self.retrieve_evidence(context)
        sector = sector_dependency_service.infer_sector(context.get("company_name", ""), context.get("ticker", ""), evidence)
        context["sector"] = sector
        dependency_info = sector_dependency_service.relevant_dependencies(sector, context.get("parsed_scenario", {}))
        if sector == "unknown":
            limitations = [
                "Sector could not be inferred from company/ticker or local evidence.",
                "Sector-level exposure should be treated as generic until more evidence is available.",
                "Agent output is not financial advice and does not predict stock prices.",
            ]
        else:
            limitations = [
                "Sector mapping is rule-based and depends on local evidence.",
                "Sector findings are not company-specific unless company evidence is also available.",
                "Agent output is not financial advice and does not predict stock prices.",
            ]
        if not evidence:
            return self.no_evidence_output(
                "Not enough local evidence was available for sector analysis.",
                limitations,
            )
        findings = [
            f"Inferred sector: {sector}. Relevant dependencies: {', '.join(dependency_info.get('relevant_dependencies', [])) or 'none found'}."
        ]
        findings.extend(self.findings_from_evidence(evidence, "Sector evidence"))
        return {
            "agent_name": self.agent_name,
            "agent_key": self.agent_key,
            "status": "success",
            "summary": f"Sector analysis produced a {sector} sector view with evidence-limited dependency checks.",
            "key_findings": findings,
            "evidence_used": evidence,
            "confidence": self.confidence_from_evidence(evidence, "Sector inference is rule-based."),
            "limitations": limitations,
            "validation_warnings": [],
            "details": dependency_info,
        }
