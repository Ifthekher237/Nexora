from backend.app.services.risk.scoring_engine import clamp_score, combine_scores, risk_level


def test_score_values_are_clamped_between_zero_and_100() -> None:
    assert clamp_score(-10) == 0
    assert clamp_score(120) == 100


def test_risk_level_mapping_works() -> None:
    assert risk_level(10) == "very_low"
    assert risk_level(35) == "low"
    assert risk_level(55) == "moderate"
    assert risk_level(75) == "high"
    assert risk_level(90) == "very_high"


def test_combine_scores_returns_valid_overall_score() -> None:
    result = combine_scores(
        evidence_strength_score=80,
        reasoning_confidence_score=0.7,
        causal_chain_score=60,
        exposure_score=65,
        macro_risk_score=70,
        source_diversity=80,
    )

    assert 0 <= result["overall_risk_score"] <= 100
    assert result["overall_risk_level"] in {"low", "moderate", "high", "very_high"}
