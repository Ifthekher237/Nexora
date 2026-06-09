"""Explain confidence separately from risk or answer severity."""

from __future__ import annotations

from typing import Any


DISTINCTION = (
    "High risk does not mean high confidence. Low confidence does not mean low risk; "
    "confidence describes how well the saved evidence supports the output."
)


def explain_confidence(
    target_output: dict[str, Any],
    coverage: dict[str, Any],
    unsupported_claims: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    confidence = target_output.get("confidence") if isinstance(target_output.get("confidence"), dict) else {}
    level = str(confidence.get("level") or "unknown")
    try:
        score = max(0.0, min(1.0, float(confidence.get("score") or 0.0)))
    except (TypeError, ValueError):
        score = 0.0

    limitations = target_output.get("limitations") if isinstance(target_output.get("limitations"), list) else []
    warnings = target_output.get("validation_warnings") if isinstance(target_output.get("validation_warnings"), list) else []
    unsupported_count = len(unsupported_claims or [])
    factors = [
        f"Saved confidence level is {level} with score {score:.2f}.",
        f"Evidence coverage is {coverage.get('level')} with score {float(coverage.get('score') or 0.0):.2f}.",
        f"{coverage.get('sources_used', 0)} source(s) and {coverage.get('unique_documents', 0)} unique document(s) were available.",
        f"Average retrieval score is {float(coverage.get('average_retrieval_score') or 0.0):.2f}.",
        f"{len(limitations)} limitation(s), {len(warnings)} validation warning(s), and {unsupported_count} unsupported-claim warning(s) were found.",
    ]
    base_reason = str(confidence.get("reason") or "The saved output did not include a confidence reason.")
    explanation = f"{base_reason} {DISTINCTION}"
    return {
        "level": level,
        "score": round(score, 4),
        "explanation": explanation,
        "factors": factors,
        "distinction": DISTINCTION,
    }
