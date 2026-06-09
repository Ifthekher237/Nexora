from backend.app.services.reasoning.causal_chain_service import build_causal_chain
from backend.app.services.reasoning.macro_impact_service import identify_macro_channels
from backend.app.services.reasoning.operational_exposure_service import identify_operational_exposures


def test_causal_chain_service_returns_expected_oil_steps() -> None:
    chain = build_causal_chain({"scenario_type": "oil_price_shock"})

    assert chain[0]["cause"] == "Oil price increase"
    assert any("margin" in step["effect"].lower() for step in chain)


def test_macro_impact_service_identifies_interest_rates() -> None:
    channels = identify_macro_channels(
        {"scenario_type": "interest_rate_change", "macro_trigger": "interest rates"},
        "interest rates rise",
    )

    assert "interest rates" in channels


def test_operational_exposure_service_returns_expected_areas() -> None:
    exposures = identify_operational_exposures({"scenario_type": "oil_price_shock"})

    assert "cost structure" in exposures["areas"]
    assert "pricing power" in exposures["areas"]
