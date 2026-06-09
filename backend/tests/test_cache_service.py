import time

from backend.app.schemas.performance import CacheClearRequest
from backend.app.services.performance import cache_service


def test_cache_get_set_works() -> None:
    cache_service.clear("retrieval")
    key = cache_service.make_cache_key({"query": "financial risk"}, prefix="test")

    assert cache_service.get("retrieval", key) is None
    assert cache_service.set("retrieval", key, {"result": 1}, ttl_seconds=30, disk=False)
    assert cache_service.get("retrieval", key) == {"result": 1}


def test_cache_ttl_expiration() -> None:
    cache_service.clear("response")
    key = cache_service.make_cache_key({"short": "ttl"}, prefix="test")

    cache_service.set("response", key, {"value": "expires"}, ttl_seconds=0, disk=False)
    time.sleep(0.01)

    assert cache_service.get("response", key) is None


def test_cache_namespace_clear() -> None:
    cache_service.clear("metadata")
    key = cache_service.make_cache_key({"index": "metadata"}, prefix="test")
    cache_service.set("metadata", key, {"rows": []}, ttl_seconds=30, disk=False)

    result = cache_service.clear("metadata")

    assert result["cleared"]["metadata"] >= 1
    assert cache_service.get("metadata", key) is None


def test_cache_clear_schema() -> None:
    request = CacheClearRequest(namespace="all")

    assert request.namespace == "all"
