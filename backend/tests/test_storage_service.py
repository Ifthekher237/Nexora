from backend.app.services.ingestion import storage_service


def test_storage_directories_can_be_created(tmp_path, monkeypatch) -> None:
    raw_root = tmp_path / "raw"
    metadata_root = tmp_path / "metadata"
    monkeypatch.setattr(storage_service, "storage_root", lambda: raw_root)
    monkeypatch.setattr(storage_service, "metadata_root", lambda: metadata_root)

    storage_service.ensure_storage_directories()

    assert (raw_root / "sec").exists()
    assert (raw_root / "rss").exists()
    assert (raw_root / "local_uploads").exists()
    assert metadata_root.exists()


def test_content_hash_for_file_is_stable(tmp_path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("Nexora ingestion test", encoding="utf-8")

    first_hash = storage_service.content_hash_for_file(sample)
    second_hash = storage_service.content_hash_for_file(sample)

    assert first_hash == second_hash
    assert len(first_hash) == 64
