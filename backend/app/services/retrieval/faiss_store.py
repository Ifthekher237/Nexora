"""Local FAISS vector store adapter."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from backend.app.services.retrieval.retrieval_metadata_service import faiss_dir


class FaissStoreError(RuntimeError):
    """Raised when FAISS cannot complete an operation."""


def index_path() -> Path:
    return faiss_dir() / "nexora.index"


def id_map_path() -> Path:
    return faiss_dir() / "id_map.json"


def _load_faiss():
    try:
        import faiss

        return faiss
    except Exception as exc:
        raise FaissStoreError("faiss-cpu is not installed or could not be imported.") from exc


def faiss_status() -> dict[str, object]:
    available = True
    error = ""
    try:
        _load_faiss()
    except FaissStoreError as exc:
        available = False
        error = str(exc)

    id_map = load_id_map() if id_map_path().exists() else []
    return {
        "available": available,
        "error": error,
        "index_path": str(index_path()),
        "index_exists": index_path().exists(),
        "mapped_vectors": len(id_map),
    }


def load_id_map() -> list[str]:
    if not id_map_path().exists():
        return []
    return json.loads(id_map_path().read_text(encoding="utf-8"))


def save_id_map(vector_ids: list[str]) -> None:
    faiss_dir().mkdir(parents=True, exist_ok=True)
    id_map_path().write_text(json.dumps(vector_ids, indent=2), encoding="utf-8")


def add_vectors(vectors: np.ndarray, vector_ids: list[str], rebuild: bool = False) -> None:
    if len(vector_ids) != len(vectors):
        raise FaissStoreError("Vector ID count does not match vector count.")
    if len(vector_ids) == 0:
        return

    faiss = _load_faiss()
    faiss_dir().mkdir(parents=True, exist_ok=True)
    vectors = np.asarray(vectors, dtype=np.float32)
    dimension = int(vectors.shape[1])

    if rebuild or not index_path().exists():
        index = faiss.IndexFlatIP(dimension)
        id_map: list[str] = []
    else:
        index = faiss.read_index(str(index_path()))
        id_map = load_id_map()
        if index.d != dimension:
            raise FaissStoreError(
                f"Existing FAISS dimension {index.d} does not match new dimension {dimension}."
            )

    index.add(vectors)
    id_map.extend(vector_ids)
    faiss.write_index(index, str(index_path()))
    save_id_map(id_map)


def search_vectors(query_vector: np.ndarray, top_k: int) -> list[dict[str, object]]:
    if not index_path().exists():
        raise FaissStoreError("FAISS index file does not exist. Build the vector index first.")

    faiss = _load_faiss()
    index = faiss.read_index(str(index_path()))
    if index.ntotal == 0:
        return []

    id_map = load_id_map()
    if not id_map:
        raise FaissStoreError("FAISS ID map is missing or empty.")

    query_vector = np.asarray(query_vector, dtype=np.float32)
    if query_vector.ndim == 1:
        query_vector = query_vector.reshape(1, -1)

    search_k = min(max(top_k, 1), int(index.ntotal))
    scores, ids = index.search(query_vector, search_k)
    results: list[dict[str, object]] = []
    for score, internal_id in zip(scores[0], ids[0], strict=False):
        if internal_id < 0 or internal_id >= len(id_map):
            continue
        results.append(
            {
                "vector_id": id_map[int(internal_id)],
                "score": float(score),
            }
        )
    return results


def search_all_vectors(query_vector: np.ndarray) -> list[dict[str, object]]:
    if not index_path().exists():
        raise FaissStoreError("FAISS index file does not exist. Build the vector index first.")

    faiss = _load_faiss()
    index = faiss.read_index(str(index_path()))
    if index.ntotal == 0:
        return []
    return search_vectors(query_vector, int(index.ntotal))
