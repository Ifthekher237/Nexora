"""Simple rule-based query understanding for Phase 5 RAG."""

from __future__ import annotations

import re
from typing import Any


RISK_KEYWORDS = [
    "interest rate",
    "inflation",
    "oil price",
    "debt",
    "revenue",
    "liquidity",
    "supply chain",
    "regulation",
]

MACRO_KEYWORDS = {
    "inflation",
    "interest rate",
    "central bank",
    "fed",
    "gdp",
    "unemployment",
    "oil price",
    "macro",
}

DOCUMENT_KEYWORDS = {
    "document",
    "filing",
    "report",
    "source",
    "section",
    "evidence",
    "transcript",
}


def _possible_ticker(question: str) -> str | None:
    matches = re.findall(r"\b[A-Z]{1,5}\b", question)
    stopwords = {"SEC", "ASX", "RSS", "CEO", "CFO", "USA", "USD", "ETF", "IPO"}
    for match in matches:
        if match not in stopwords:
            return match
    return None


def understand_query(question: str) -> dict[str, Any]:
    clean_question = " ".join(question.strip().split())
    lowered = clean_question.lower()
    ticker = _possible_ticker(clean_question)
    risk_keywords = [keyword for keyword in RISK_KEYWORDS if keyword in lowered]

    if not clean_question:
        query_type = "unknown"
    elif risk_keywords or "risk" in lowered or "exposure" in lowered:
        query_type = "risk_question"
    elif any(keyword in lowered for keyword in MACRO_KEYWORDS):
        query_type = "macro_question"
    elif ticker:
        query_type = "company_specific_question"
    elif any(keyword in lowered for keyword in DOCUMENT_KEYWORDS):
        query_type = "document_question"
    elif any(word in lowered for word in {"company", "ticker", "business", "financial"}):
        query_type = "general_financial_question"
    else:
        query_type = "unknown"

    return {
        "question": clean_question,
        "query_type": query_type,
        "possible_ticker": ticker,
        "risk_keywords": risk_keywords,
    }
