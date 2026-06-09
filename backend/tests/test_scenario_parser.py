from backend.app.services.reasoning.scenario_parser import parse_scenario


def test_scenario_parser_detects_oil_price_shock_and_numerical_shock() -> None:
    parsed = parse_scenario(
        "What happens to Qantas if oil prices rise by 25% over the next 6 months?",
        company_name="Qantas Airways",
        ticker="QAN",
        market="ASX",
    )

    assert parsed["scenario_type"] == "oil_price_shock"
    assert parsed["numerical_shock"] == "25%"
    assert parsed["time_horizon"] == "6 months"
    assert parsed["ticker"] == "QAN"


def test_scenario_parser_detects_interest_rate_change() -> None:
    parsed = parse_scenario("What financial risks could appear if interest rates increase by 1%?")

    assert parsed["scenario_type"] == "interest_rate_change"
    assert parsed["numerical_shock"] == "1%"
    assert parsed["macro_trigger"] == "interest rates"
