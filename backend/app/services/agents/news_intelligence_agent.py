"""News intelligence agent using only locally ingested RSS/news evidence."""

from __future__ import annotations

from typing import Any

from backend.app.services.agents import agent_evidence_service
from backend.app.services.agents.base_agent import BaseFinancialAgent


class NewsIntelligenceAgent(BaseFinancialAgent):
    agent_key = "news_intelligence_agent"
    agent_name = "News Intelligence Agent"
    description = "Reviews locally ingested RSS/news context, recency, and event relevance."
    focus_terms = ["news", "rss", "recent", "event", "market context", "financial news"]

    def retrieve_evidence(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        return agent_evidence_service.retrieve_agent_evidence(
            scenario=context["scenario"],
            focus_terms=self.evidence_query_terms(context),
            top_k=context["top_k"],
            vector_store=context.get("vector_store", "faiss"),
            filters=context.get("filters", {}),
            source_type="rss",
        )

    def run(self, context: dict[str, Any], memory: dict[str, Any]) -> dict[str, Any]:
        evidence = self.retrieve_evidence(context)
        if not evidence:
            return self.no_evidence_output(
                "No locally ingested RSS/news evidence was retrieved for this scenario.",
                [
                    "News agent only uses local Nexora RSS/news records and does not browse the web.",
                    "Ingest RSS sources and rebuild the vector index for fresher local news context.",
                    "Agent output is not financial advice and does not predict stock prices.",
                ],
            )
        dates = sorted(
            {
                str((item.get("metadata") or {}).get("published_at", ""))
                for item in evidence
                if (item.get("metadata") or {}).get("published_at")
            },
            reverse=True,
        )
        findings = self.findings_from_evidence(evidence, "Local news evidence")
        if dates:
            findings.insert(0, f"Most recent local news/RSS timestamp in retrieved evidence: {dates[0]}.")
        return {
            "agent_name": self.agent_name,
            "agent_key": self.agent_key,
            "status": "success",
            "summary": "News intelligence found local RSS/news evidence relevant to the scenario context.",
            "key_findings": findings,
            "evidence_used": evidence,
            "confidence": self.confidence_from_evidence(evidence),
            "limitations": [
                "News context is limited to locally ingested RSS/news records.",
                "The agent does not browse the web for current events.",
                "Agent output is not financial advice and does not predict stock prices.",
            ],
            "validation_warnings": [],
            "details": {"published_dates": dates[:10]},
        }
