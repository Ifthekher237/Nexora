"""Local embedding model service for Nexora retrieval."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

import numpy as np

from backend.app.core.config import get_retrieval_config


logger = logging.getLogger(__name__)


class EmbeddingServiceError(RuntimeError):
    """Raised when the local embedding model cannot be used."""


def default_embedding_model() -> str:
    return get_retrieval_config().get("embedding", {}).get(
        "default_model", "BAAI/bge-small-en-v1.5"
    )


def _normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms


def _device_from_config() -> str:
    configured = get_retrieval_config().get("embedding", {}).get("device", "auto")
    if configured != "auto":
        return configured

    try:
        import torch

        if torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass

    return "cpu"


@lru_cache(maxsize=2)
def load_embedding_model(model_name: str | None = None) -> Any:
    selected_model = model_name or default_embedding_model()
    device = _device_from_config()

    try:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model from local cache | model=%s | device=%s", selected_model, device)
        return SentenceTransformer(
            selected_model,
            device=device,
            local_files_only=True,
        )
    except Exception as exc:
        logger.warning("Embedding model local cache load failed, retrying online: %s", exc)

    try:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model online if needed | model=%s | device=%s", selected_model, device)
        return SentenceTransformer(selected_model, device=device)
    except Exception as exc:
        logger.error("Embedding model load failed: %s", exc)
        raise EmbeddingServiceError(
            f"Local embedding model '{selected_model}' could not be loaded. "
            "Install dependencies and allow the first Hugging Face download if needed."
        ) from exc


def embedding_status() -> dict[str, object]:
    try:
        import sentence_transformers  # noqa: F401

        package_available = True
    except Exception:
        package_available = False

    return {
        "default_model": default_embedding_model(),
        "device": _device_from_config(),
        "sentence_transformers_available": package_available,
        "loaded_in_process": load_embedding_model.cache_info().currsize > 0,
        "local_first": get_retrieval_config().get("embedding", {}).get("local_first", True),
    }


def embed_texts(texts: list[str], model_name: str | None = None) -> np.ndarray:
    if not texts:
        return np.empty((0, 0), dtype=np.float32)

    model = load_embedding_model(model_name)
    batch_size = int(get_retrieval_config().get("retrieval", {}).get("batch_size", 32))
    normalize = bool(get_retrieval_config().get("retrieval", {}).get("normalize_embeddings", True))

    try:
        vectors = model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
    except Exception as exc:
        raise EmbeddingServiceError(f"Embedding generation failed: {exc}") from exc

    vectors = np.asarray(vectors, dtype=np.float32)
    if vectors.ndim == 1:
        vectors = vectors.reshape(1, -1)
    if normalize:
        vectors = _normalize(vectors)
    return vectors.astype(np.float32)


def embed_query(query: str, model_name: str | None = None) -> np.ndarray:
    # BGE models work well when the query intent is explicit.
    query_text = f"Represent this sentence for searching relevant passages: {query}"
    return embed_texts([query_text], model_name=model_name)


def embedding_dimension(model_name: str | None = None) -> int:
    sample = embed_texts(["dimension check"], model_name=model_name)
    return int(sample.shape[1])
