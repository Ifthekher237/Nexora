from backend.app.services.deployment import deployment_readiness_service, final_report_service


def test_deployment_readiness_returns_structured_result(monkeypatch) -> None:
    monkeypatch.setattr(
        deployment_readiness_service.final_report_service,
        "save_deployment_report",
        lambda report, markdown="": {"saved": False, "report_id": "TEST_REPORT", "json_path": "", "markdown_path": ""},
    )

    result = deployment_readiness_service.run_readiness_check(save=True)

    assert "readiness_score" in result
    assert result["readiness_level"] in {"early", "local_ready", "portfolio_ready", "enterprise_planning_ready"}
    assert result["checks"]
    assert result["actual_cloud_deployment"] is False


def test_deployment_readiness_reports_missing_files_honestly() -> None:
    result = deployment_readiness_service.run_readiness_check(
        save=False,
        extra_required_files=["definitely_missing_phase_12_file.txt"],
    )

    matching = [
        check
        for check in result["checks"]
        if "definitely_missing_phase_12_file.txt" in check["name"]
    ]
    assert matching
    assert matching[0]["status"] == "fail"


def test_deployment_status_works() -> None:
    status = deployment_readiness_service.deployment_status()

    assert status["status"] == "ready"
    assert status["local_first"] is True
    assert status["actual_cloud_deployment"] is False


def test_final_report_service_can_generate_report(monkeypatch) -> None:
    saved = {}

    def fake_save(report, markdown=""):
        saved["markdown"] = markdown
        return {"saved": False, "report_id": "FINAL_TEST", "json_path": "", "markdown_path": ""}

    monkeypatch.setattr(final_report_service, "save_deployment_report", fake_save)

    report = final_report_service.generate_final_project_report()

    assert report["status"] == "success"
    assert report["report_id"] == "FINAL_TEST"
    assert "Nexora Final Project Report" in saved["markdown"]
