import builtins

from backend.app.services.performance import resource_monitor


def test_resource_monitor_returns_standard_fields() -> None:
    snapshot = resource_monitor.snapshot()

    assert snapshot["status"] in {"ok", "degraded"}
    assert snapshot["python_version"]
    assert snapshot["platform"]
    assert "apple_silicon_note" in snapshot


def test_resource_monitor_handles_missing_psutil(monkeypatch) -> None:
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "psutil":
            raise ImportError("psutil intentionally unavailable")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    snapshot = resource_monitor.snapshot()

    assert snapshot["psutil_available"] is False
    assert "psutil is unavailable" in snapshot["fallback_note"]
