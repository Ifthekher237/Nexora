"""Central coordinator for Nexora's Phase 5 financial RAG pipeline."""

from __future__ import annotations

import logging
from typing import Any

from backend.app.core.config import PROJECT_ROOT, get_rag_config
from backend.app.services.ingestion.metadata_service import utc_now_iso
from backend.app.services.ollama_service import (
    OllamaServiceError,
    call_ollama_model,
    check_ollama_running,
    list_local_models,
)
from backend.app.services.rag import (
    citation_service,
    confidence_service,
    context_builder,
    hallucination_guard,
    prompt_builder,
    query_understanding_service,
    rag_response_service,
)
from backend.app.services.retrieval import retrieval_service, vector_store_manager


logger = logging.getLogger(__name__)


class RAGManagerError(RuntimeError):
    """Raised when a RAG request is invalid before execution."""


def _config_section(name: str) -> dict[str, Any]:
    return get_rag_config().get(name, {})


def _default_model() -> str:
    return str(_config_section("llm").get("default_model", "llama3.1:8b"))


def _fallback_model() -> str:
    return str(_config_section("llm").get("fallback_model", "mistral:7b"))


def _default_top_k() -> int:
    return int(_config_section("rag").get("default_top_k", 5))


def _max_top_k() -> int:
    return int(_config_section("rag").get("max_top_k", 10))


def _default_vector_store() -> str:
    return str(_config_section("retrieval").get("default_vector_store", "faiss"))


def _filters_dict(filters: Any) -> dict[str, str | None]:
    if filters is None:
        return {
            "ticker": None,
            "source_type": None,
            "document_type": None,
            "market": None,
            "section_hint": None,
        }
    if hasattr(filters, "model_dump"):
        raw = filters.model_dump()
    elif isinstance(filters, dict):
        raw = filters
    else:
        raw = {}
    return {
        "ticker": raw.get("ticker") or None,
        "source_type": raw.get("source_type") or None,
        "document_type": raw.get("document_type") or None,
        "market": raw.get("market") or None,
        "section_hint": raw.get("section_hint") or None,
    }


def _validated_top_k(value: int | None) -> int:
    top_k = int(value or _default_top_k())
    if top_k < 1:
        raise RAGManagerError("top_k must be at least 1.")
    if top_k > _max_top_k():
        raise RAGManagerError(f"top_k cannot exceed {_max_top_k()} for RAG requests.")
    return top_k


def _llm_options() -> dict[str, Any]:
    llm_config = _config_section("llm")
    options: dict[str, Any] = {
        "temperature": float(llm_config.get("temperature", 0.2)),
        "top_p": float(llm_config.get("top_p", 0.9)),
    }
    max_tokens = llm_config.get("max_tokens")
    if max_tokens is not None:
        options["num_predict"] = int(max_tokens)
    return options


def _base_limitations(extra: list[str] | None = None) -> list[str]:
    limitations = [
        "This answer is limited to the documents retrieved from the local Nexora vector index.",
        "Nexora does not provide investment advice, buy/sell/hold calls, or stock price predictions.",
    ]
    for item in extra or []:
        if item and item not in limitations:
            limitations.append(item)
    return limitations


def _retrieval_summary(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "results_found": int(context.get("results_found", 0)),
        "evidence_used": int(context.get("evidence_used", 0)),
        "min_score": float(context.get("min_score", context_builder.configured_min_score())),
    }


def _save_response(response: dict[str, Any]) -> dict[str, Any]:
    try:
        rag_response_service.save_response(response)
    except rag_response_service.RAGResponseStorageError as exc:
        logger.exception("RAG response save failed")
        response.setdefault("limitations", []).append(str(exc))
        response["error_message"] = "; ".join(
            item for item in [response.get("error_message", ""), str(exc)] if item
        )
        if response.get("status") == "success":
            response["status"] = "partial_success"
    return response


def _error_response(
    question: str,
    model: str,
    filters: dict[str, str | None],
    message: str,
    query_type: str = "unknown",
    retrieval_summary: dict[str, Any] | None = None,
    sources: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    response = {
        "response_id": rag_response_service.generate_response_id(question),
        "question": question,
        "answer": message,
        "model": model,
        "query_type": query_type,
        "confidence": {
            "level": "low",
            "score": 0.0,
            "reason": "The RAG request could not complete successfully.",
        },
        "sources": sources or [],
        "retrieval_summary": retrieval_summary
        or {
            "results_found": 0,
            "evidence_used": 0,
            "min_score": context_builder.configured_min_score(),
        },
        "limitations": _base_limitations([message]),
        "status": "error",
        "created_at": utc_now_iso(),
        "filters": filters,
        "error_message": message,
    }
    return _save_response(response)


def rag_status() -> dict[str, Any]:
    rag_config = _config_section("rag")
    retrieval_status: dict[str, object]
    try:
        retrieval_status = vector_store_manager.retrieval_system_status()
    except Exception as exc:  # pragma: no cover - defensive status endpoint guard
        retrieval_status = {"status": "error", "message": str(exc)}

    running = check_ollama_running()
    installed = list_local_models() if running else []
    return {
        "status": "ready" if retrieval_status.get("status") == "ready" else "degraded",
        "default_model": _default_model(),
        "fallback_model": _fallback_model(),
        "default_top_k": _default_top_k(),
        "max_top_k": _max_top_k(),
        "min_retrieval_score": float(rag_config.get("min_retrieval_score", 0.25)),
        "require_citations": bool(rag_config.get("require_citations", True)),
        "save_rag_outputs": rag_response_service.save_enabled(),
        "response_output_dir": str(
            PROJECT_ROOT
            / rag_config.get("response_output_dir", "data/rag_outputs/responses")
        ),
        "response_index_csv": str(rag_response_service.response_index_csv_path()),
        "response_index_json": str(rag_response_service.response_index_json_path()),
        "retrieval_status": retrieval_status,
        "ollama_running": running,
        "installed_models": installed,
    }


def _retrieve_and_build_context(
    question: str,
    top_k: int,
    vector_store: str,
    filters: dict[str, str | None],
) -> dict[str, Any]:
    retrieval_result = retrieval_service.search(
        query=question,
        top_k=top_k,
        vector_store=vector_store,
        filters=filters,
    )
    return context_builder.build_context(retrieval_result)


def ask_question(
    question: str,
    top_k: int | None = None,
    model: str | None = None,
    filters: Any = None,
    vector_store: str | None = None,
) -> dict[str, Any]:
    clean_question = " ".join(question.strip().split())
    selected_model = (model or _default_model()).strip()
    selected_store = (vector_store or _default_vector_store()).strip().lower()
    normalized_filters = _filters_dict(filters)
    query_info = query_understanding_service.understand_query(clean_question)

    if not clean_question:
        raise RAGManagerError("Question cannot be empty.")
    selected_top_k = _validated_top_k(top_k)

    logger.info(
        "RAG request received | question=%s | model=%s | top_k=%s | filters=%s",
        clean_question,
        selected_model,
        selected_top_k,
        normalized_filters,
    )

    try:
        context = _retrieve_and_build_context(
            clean_question,
            selected_top_k,
            selected_store,
            normalized_filters,
        )
    except Exception as exc:
        logger.exception("RAG retrieval failed")
        return _error_response(
            clean_question,
            selected_model,
            normalized_filters,
            f"Retrieval failed: {exc}",
            query_type=query_info["query_type"],
        )

    summary = _retrieval_summary(context)
    logger.info(
        "RAG retrieval completed | results_found=%s | evidence_used=%s",
        summary["results_found"],
        summary["evidence_used"],
    )

    evidence = context["evidence"]
    sources = citation_service.build_sources(evidence)
    sources_payload = [source.model_dump() for source in sources]
    blocked, block_reason = hallucination_guard.should_block_without_llm(evidence)
    if blocked:
        confidence = confidence_service.estimate_confidence(evidence, clean_question, summary)
        response = {
            "response_id": rag_response_service.generate_response_id(clean_question),
            "question": clean_question,
            "answer": hallucination_guard.insufficient_evidence_answer(
                clean_question,
                block_reason,
            ),
            "model": selected_model,
            "query_type": query_info["query_type"],
            "confidence": confidence,
            "sources": sources_payload,
            "retrieval_summary": summary,
            "limitations": _base_limitations(context.get("limitations", []) + [block_reason]),
            "status": "insufficient_evidence",
            "created_at": utc_now_iso(),
            "filters": normalized_filters,
            "error_message": "",
        }
        logger.info("RAG request blocked before LLM | reason=%s", block_reason)
        return _save_response(response)

    prompt = prompt_builder.build_prompt(
        clean_question,
        context["evidence_context"],
        query_understanding=query_info,
    )

    try:
        answer = call_ollama_model(
            prompt=prompt,
            model=selected_model,
            timeout=180.0,
            options=_llm_options(),
        )
        logger.info("RAG Ollama call completed | model=%s", selected_model)
    except OllamaServiceError as exc:
        logger.warning("RAG Ollama call failed: %s", exc)
        return _error_response(
            clean_question,
            selected_model,
            normalized_filters,
            str(exc),
            query_type=query_info["query_type"],
            retrieval_summary=summary,
            sources=sources_payload,
        )

    guard_result = hallucination_guard.validate_answer(answer, sources)
    confidence = confidence_service.estimate_confidence(evidence, clean_question, summary)
    limitations = _base_limitations(
        context.get("limitations", []) + guard_result.get("limitations", [])
    )
    response = {
        "response_id": rag_response_service.generate_response_id(clean_question),
        "question": clean_question,
        "answer": guard_result["answer"],
        "model": selected_model,
        "query_type": query_info["query_type"],
        "confidence": confidence,
        "sources": sources_payload,
        "retrieval_summary": summary,
        "limitations": limitations,
        "status": guard_result.get("status", "success"),
        "created_at": utc_now_iso(),
        "filters": normalized_filters,
        "error_message": "",
    }
    logger.info(
        "RAG response built | confidence=%s | status=%s",
        confidence.get("score"),
        response["status"],
    )
    return _save_response(response)


def evidence_only(
    question: str,
    top_k: int | None = None,
    filters: Any = None,
    vector_store: str | None = None,
) -> dict[str, Any]:
    clean_question = " ".join(question.strip().split())
    if not clean_question:
        raise RAGManagerError("Question cannot be empty.")
    selected_top_k = _validated_top_k(top_k)
    selected_store = (vector_store or _default_vector_store()).strip().lower()
    normalized_filters = _filters_dict(filters)
    query_info = query_understanding_service.understand_query(clean_question)
    context = _retrieve_and_build_context(
        clean_question,
        selected_top_k,
        selected_store,
        normalized_filters,
    )
    sources = citation_service.build_sources(context["evidence"])
    return {
        "question": clean_question,
        "query_type": query_info["query_type"],
        "evidence_context": context["evidence_context"],
        "sources": [source.model_dump() for source in sources],
        "retrieval_summary": _retrieval_summary(context),
        "limitations": _base_limitations(context.get("limitations", [])),
        "status": "success" if sources else "insufficient_evidence",
    }
