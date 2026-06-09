"""Company analysis agent."""

from __future__ import annotations

from typing import Any

from backend.app.services.agents.base_agent import BaseFinancialAgent


class CompanyAnalysisAgent(BaseFinancialAgent):
    agent_key = "company_analysis_agent"
    agent_name = "Company Analysis Agent"
    description = "Reviews company-specific exposure, ticker evidence, filings, revenue, cost, debt, and liquidity mentions."
    focus_terms = ["company exposure", "revenue", "cost", "debt", "liquidity", "cash flow", "filing", "annual report"]

    def evidence_query_terms(self, context: dict[str, Any]) -> list[str]:
        terms = list(self.focus_terms)
        if context.get("ticker"):
            terms.insert(0, str(context["ticker"]))
        if context.get("company_name"):
            terms.insert(0, str(context["company_name"]))
        return terms

    def run(self, context: dict[str, Any], memory: dict[str, Any]) -> dict[str, Any]:
        if not context.get("company_name") and not context.get("ticker"):
            return self.no_evidence_output(
                "No company or ticker was supplied, so company-specific exposure cannot be assessed.",
                [
                    "Provide a company name or ticker to run company-level analysis.",
                    "Retrieved scenario evidence should be treated as general context, not company-specific support.",
                    "Agent output is not financial advice and does not predict stock prices.",
                ],
            )
        evidence = self.retrieve_evidence(context)
        if not evidence:
            return self.no_evidence_output(
                "No company-specific evidence was retrieved for the supplied company/ticker.",
                [
                    "Company-specific documents may need to be ingested and indexed first.",
                    "The agent cannot infer company exposure without local evidence.",
                    "Agent output is not financial advice and does not predict stock prices.",
                ],
            )
        findings = self.findings_from_evidence(evidence, "Company evidence")
        docs = sorted({item.get("source_document_id", "") for item in evidence if item.get("source_document_id")})
        return {
            "agent_name": self.agent_name,
            "agent_key": self.agent_key,
            "status": "success",
            "summary": f"Company analysis found {len(evidence)} local evidence item(s) across {len(docs)} document(s).",
            "key_findings": findings,
            "evidence_used": evidence,
            "confidence": self.confidence_from_evidence(evidence),
            "limitations": [
                "Company findings depend on available local filings, news, or uploaded documents.",
                "The agent does not infer missing financial ratios or company facts.",
                "Agent output is not financial advice and does not predict stock prices.",
            ],
            "validation_warnings": [],
            "details": {"source_documents_found": docs},
        }
