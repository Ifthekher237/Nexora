from backend.app.core.config import get_retrieval_config
from backend.app.services.retrieval.embedding_service import default_embedding_model, embedding_status


def test_embedding_config_loads() -> None:
    config = get_retrieval_config()

    assert config["embedding"]["default_model"] == "BAAI/bge-small-en-v1.5"
    assert config["retrieval"]["default_vector_store"] == "faiss"


def test_embedding_status_does_not_force_model_load() -> None:
    status = embedding_status()

    assert status["default_model"] == default_embedding_model()
    assert status["device"] in {"cpu", "mps", "cuda"}
    assert "sentence_transformers_available" in status
