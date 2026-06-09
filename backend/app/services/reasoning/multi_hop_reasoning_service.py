"""Multi-hop reasoning helpers for Phase 6."""

from __future__ import annotations

from typing import Any

from backend.app.services.ollama_service import call_ollama_model


def llm_options(llm_config: dict[str, Any]) -> dict[str, Any]:
    options = {
        "temperature": float(llm_config.get("temperature", 0.2)),
        "top_p": float(llm_config.get("top_p", 0.9)),
    }
    max_tokens = llm_config.get("max_tokens")
    if max_tokens is not None:
        options["num_predict"] = int(max_tokens)
    return options


def run_llm_reasoning(prompt: str, model: str, llm_config: dict[str, Any]) -> str:
    return call_ollama_model(
        prompt=prompt,
        model=model,
        timeout=240.0,
        options=llm_options(llm_config),
    )


def build_financial_exposure_analysis(
    parsed_scenario: dict[str, Any],
    company_map: dict[str, Any],
    sector_dependencies: dict[str, Any],
    macro_channels: list[str],
    operational_exposures: dict[str, Any],
    evidence_map: list[dict[str, Any]],
) -> dict[str, str]:
    evidence_refs = ", ".join(item["source_number"] for item in evidence_map[:4]) or "no qualifying sources"
    areas = ", ".join(operational_exposures.get("areas", [])) or "unknown"
    dependencies = ", ".join(sector_dependencies.get("relevant_dependencies", [])) or "unknown"
    channels = ", ".join(macro_channels) or parsed_scenario.get("macro_trigger") or "unknown"
    company_label = company_map.get("company_name") or company_map.get("ticker") or "the company"
    source_documents = company_map.get("source_documents_found", [])
    if not company_map.get("company_name") and not company_map.get("ticker"):
        company_specific = (
            "No company or ticker was specified, so company-specific exposure cannot be confirmed. "
            f"Retrieved documents should be treated as general scenario context ({evidence_refs})."
        )
    else:
        company_specific = (
            f"{company_label} has {len(source_documents)} related source document(s) in the local vector metadata. "
            f"Company-specific conclusions must be limited to retrieved sources ({evidence_refs})."
        )

    return {
        "operational_exposure": (
            f"Potential operational exposure areas: {areas}. This is inferred from the scenario "
            f"type and retrieved evidence references ({evidence_refs}); Phase 6 does not quantify exposure values."
        ),
        "macro_exposure": (
            f"Relevant macro channel(s): {channels}. Any causal claim should be treated as evidence-limited "
            f"unless supported by the cited sources."
        ),
        "sector_exposure": (
            f"Inferred sector: {company_map.get('sector', 'unknown')}. Relevant dependency checks: {dependencies}. "
            "If the sector is unknown, these are generic scenario dependencies rather than company facts."
        ),
        "company_specific_exposure": company_specific,
    }


def insufficient_evidence_direct_answer(scenario: str) -> str:
    return (
        "The available Nexora evidence is insufficient to reason through this scenario reliably. "
        "No multi-hop company impact should be treated as confirmed until relevant documents are retrieved."
    )
