from backend.app.core.config import get_app_config, get_settings
from backend.app.services.model_registry import get_available_models, get_default_model


def test_app_config_loads() -> None:
    config = get_app_config()
    settings = get_settings()

    assert config["app"]["name"] == "Nexora"
    assert settings.app_name == "Nexora"
    assert settings.local_first is True


def test_default_model_exists_in_registry() -> None:
    default_model = get_default_model()
    available_model_names = {model["name"] for model in get_available_models()}

    assert default_model == "llama3.1:8b"
    assert default_model in available_model_names
