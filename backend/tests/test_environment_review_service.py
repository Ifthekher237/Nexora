from backend.app.services.deployment import environment_review_service


def test_environment_review_handles_ollama_not_running(monkeypatch) -> None:
    monkeypatch.setattr(environment_review_service, "check_ollama_running", lambda timeout=1.0: False)
    monkeypatch.setattr(environment_review_service, "list_local_models", lambda timeout=1.0: [])

    review = environment_review_service.review_environment(check_ollama=True)

    assert review["ollama_running"] is False
    assert "warning" in review["ollama_note"].lower()
    assert review["python_version"]
