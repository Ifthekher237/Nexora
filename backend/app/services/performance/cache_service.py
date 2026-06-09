"""Small local runtime cache with TTL, namespaces, and optional disk backing."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any

from backend.app.core.config import PROJECT_ROOT, get_performance_config


logger = logging.getLogger(__name__)

VALID_NAMESPACES = {"retrieval", "metadata", "response", "status", "benchmark"}
ALL_NAMESPACE = "all"

_memory_cache: dict[str, dict[str, dict[str, Any]]] = {namespace: {} for namespace in VALID_NAMESPACES}
_stats: dict[str, dict[str, int]] = {
    namespace: {"hits": 0, "misses": 0, "sets": 0, "deletes": 0, "expired": 0, "disk_hits": 0, "disk_errors": 0}
    for namespace in VALID_NAMESPACES
}


class CacheServiceError(ValueError):
    """Raised when cache operations receive invalid input."""


def _cache_config() -> dict[str, Any]:
    return get_performance_config().get("cache", {})


def enabled() -> bool:
    return bool(_cache_config().get("enabled", True))


def allow_disk_cache() -> bool:
    return bool(_cache_config().get("allow_disk_cache", True))


def cache_dir() -> Path:
    return PROJECT_ROOT / _cache_config().get("cache_dir", "data/performance_outputs/cache")


def default_ttl_seconds() -> int:
    return int(_cache_config().get("default_ttl_seconds", 1800))


def namespace_ttl(namespace: str) -> int:
    config = _cache_config()
    if namespace == "retrieval":
        return int(config.get("retrieval_cache_ttl_seconds", default_ttl_seconds()))
    if namespace == "metadata":
        return int(config.get("metadata_cache_ttl_seconds", default_ttl_seconds()))
    if namespace == "response":
        return int(config.get("response_cache_ttl_seconds", default_ttl_seconds()))
    return default_ttl_seconds()


def _max_items() -> int:
    return max(1, int(_cache_config().get("max_items", 500)))


def _now() -> float:
    return time.time()


def _validate_namespace(namespace: str, *, allow_all: bool = False) -> str:
    clean = (namespace or "").strip().lower()
    if allow_all and clean == ALL_NAMESPACE:
        return clean
    if clean not in VALID_NAMESPACES:
        raise CacheServiceError(f"Invalid cache namespace: {namespace}")
    return clean


def make_cache_key(payload: Any, prefix: str = "") -> str:
    """Return a stable hash key for JSON-like payloads."""

    serialized = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return f"{prefix}_{digest}" if prefix else digest


def _namespace_dir(namespace: str) -> Path:
    return cache_dir() / namespace


def _disk_path(namespace: str, key: str) -> Path:
    return _namespace_dir(namespace) / f"{key}.json"


def _ensure_disk_namespace(namespace: str) -> None:
    _namespace_dir(namespace).mkdir(parents=True, exist_ok=True)


def _json_safe(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def _entry(value: Any, ttl_seconds: int) -> dict[str, Any]:
    created_at = _now()
    return {
        "value": _json_safe(value),
        "created_at": created_at,
        "expires_at": created_at + max(0, ttl_seconds),
    }


def _expired(entry: dict[str, Any]) -> bool:
    return float(entry.get("expires_at", 0)) <= _now()


def _remove_disk(namespace: str, key: str) -> None:
    path = _disk_path(namespace, key)
    try:
        if path.exists():
            path.unlink()
    except OSError as exc:
        logger.warning("Could not remove cache file | namespace=%s | key=%s | error=%s", namespace, key, exc)


def _enforce_limit(namespace: str) -> None:
    bucket = _memory_cache.setdefault(namespace, {})
    while len(bucket) > _max_items():
        oldest_key = min(bucket, key=lambda key: float(bucket[key].get("created_at", 0)))
        bucket.pop(oldest_key, None)
        _remove_disk(namespace, oldest_key)


def get(namespace: str, key: str) -> Any | None:
    namespace = _validate_namespace(namespace)
    if not enabled():
        _stats[namespace]["misses"] += 1
        return None

    bucket = _memory_cache.setdefault(namespace, {})
    entry = bucket.get(key)
    if entry:
        if _expired(entry):
            bucket.pop(key, None)
            _remove_disk(namespace, key)
            _stats[namespace]["expired"] += 1
            _stats[namespace]["misses"] += 1
            return None
        _stats[namespace]["hits"] += 1
        return _json_safe(entry.get("value"))

    if allow_disk_cache():
        path = _disk_path(namespace, key)
        if path.exists():
            try:
                disk_entry = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(disk_entry, dict) or _expired(disk_entry):
                    _remove_disk(namespace, key)
                    _stats[namespace]["expired"] += 1
                else:
                    bucket[key] = disk_entry
                    _stats[namespace]["hits"] += 1
                    _stats[namespace]["disk_hits"] += 1
                    return _json_safe(disk_entry.get("value"))
            except (OSError, json.JSONDecodeError) as exc:
                _stats[namespace]["disk_errors"] += 1
                logger.warning("Cache file could not be read | namespace=%s | key=%s | error=%s", namespace, key, exc)
                _remove_disk(namespace, key)

    _stats[namespace]["misses"] += 1
    return None


def set(namespace: str, key: str, value: Any, ttl_seconds: int | None = None, *, disk: bool | None = None) -> bool:
    namespace = _validate_namespace(namespace)
    if not enabled():
        return False
    ttl = namespace_ttl(namespace) if ttl_seconds is None else int(ttl_seconds)
    entry = _entry(value, ttl)
    _memory_cache.setdefault(namespace, {})[key] = entry
    _stats[namespace]["sets"] += 1
    _enforce_limit(namespace)

    if allow_disk_cache() if disk is None else disk:
        try:
            _ensure_disk_namespace(namespace)
            _disk_path(namespace, key).write_text(json.dumps(entry, indent=2), encoding="utf-8")
        except (OSError, TypeError, ValueError) as exc:
            _stats[namespace]["disk_errors"] += 1
            logger.warning("Cache file could not be written | namespace=%s | key=%s | error=%s", namespace, key, exc)
    logger.debug("Cache set | namespace=%s | key=%s | ttl=%s", namespace, key, ttl)
    return True


def delete(namespace: str, key: str) -> bool:
    namespace = _validate_namespace(namespace)
    removed = _memory_cache.setdefault(namespace, {}).pop(key, None) is not None
    _remove_disk(namespace, key)
    _stats[namespace]["deletes"] += 1
    return removed


def clear(namespace: str = ALL_NAMESPACE) -> dict[str, Any]:
    namespace = _validate_namespace(namespace, allow_all=True)
    namespaces = sorted(VALID_NAMESPACES) if namespace == ALL_NAMESPACE else [namespace]
    cleared: dict[str, int] = {}
    for item in namespaces:
        count = len(_memory_cache.setdefault(item, {}))
        _memory_cache[item] = {}
        disk_count = 0
        path = _namespace_dir(item)
        if path.exists():
            for cache_file in path.glob("*.json"):
                try:
                    cache_file.unlink()
                    disk_count += 1
                except OSError as exc:
                    _stats[item]["disk_errors"] += 1
                    logger.warning("Could not clear cache file | path=%s | error=%s", cache_file, exc)
        _stats[item]["deletes"] += count
        cleared[item] = count + disk_count
    logger.info("Cache cleared | namespace=%s | cleared=%s", namespace, cleared)
    return {"namespace": namespace, "cleared": cleared}


def stats() -> dict[str, Any]:
    cache_dir().mkdir(parents=True, exist_ok=True)
    namespaces: dict[str, Any] = {}
    for namespace in sorted(VALID_NAMESPACES):
        disk_files = list(_namespace_dir(namespace).glob("*.json")) if _namespace_dir(namespace).exists() else []
        namespaces[namespace] = {
            "size": len(_memory_cache.setdefault(namespace, {})),
            "keys": sorted(_memory_cache[namespace].keys())[:50],
            "disk_items": len(disk_files),
            **_stats[namespace],
        }
    return {
        "enabled": enabled(),
        "allow_disk_cache": allow_disk_cache(),
        "cache_dir": str(cache_dir()),
        "max_items": _max_items(),
        "namespaces": namespaces,
    }
