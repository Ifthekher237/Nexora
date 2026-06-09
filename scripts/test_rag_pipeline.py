"""Run a lightweight local smoke test for the Phase 5 RAG pipeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.logging_config import setup_logging
from backend.app.services.rag import rag_manager


QUESTION = "What financial risks are mentioned in the available documents?"


def main() -> int:
    setup_logging()
    print(f"Question: {QUESTION}")
    evidence = rag_manager.evidence_only(QUESTION, top_k=5)
    print("Evidence-only summary:")
    print(json.dumps(evidence["retrieval_summary"], indent=2))

    if evidence["status"] != "success":
        print("No qualifying evidence was found. The LLM stage was not run.")
        return 0

    result = rag_manager.ask_question(QUESTION, top_k=5)
    print("RAG answer status:")
    print(json.dumps(
        {
            "status": result.get("status"),
            "response_id": result.get("response_id"),
            "confidence": result.get("confidence"),
            "source_count": len(result.get("sources", [])),
            "error_message": result.get("error_message", ""),
        },
        indent=2,
    ))

    if result.get("status") == "error":
        print(
            "The retrieval/context stages worked, but the LLM answer stage did not complete. "
            "Start Ollama with `ollama serve` or open the Ollama app, then rerun this script."
        )
        return 0 if "Ollama" in result.get("error_message", "") else 1

    print("RAG pipeline smoke test completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
