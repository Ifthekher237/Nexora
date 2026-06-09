from backend.app.core.config import get_ingestion_config


def test_ingestion_config_loads() -> None:
    config = get_ingestion_config()

    assert config["ingestion"]["storage_root"] == "data/raw"
    assert config["ingestion"]["metadata_root"] == "data/metadata"
    assert config["sources"]["sec"]["enabled"] is True
    assert config["sources"]["rss"]["feeds"]
