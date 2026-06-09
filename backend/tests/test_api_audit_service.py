from backend.app.services.deployment import api_audit_service


def test_api_audit_returns_registered_routes() -> None:
    audit = api_audit_service.audit_api_routes()

    assert audit["status"] == "success"
    assert audit["route_count"] > 0
    paths = {route["path"] for route in audit["routes"]}
    assert "/deployment/status" in paths
    assert "deployment" in audit["groups"]
