import pytest

from backend.app.services.retrieval.search_filter_service import (
    RetrievalFilterError,
    apply_filters,
    normalize_filters,
)


def test_search_filters_validate_and_drop_empty_values() -> None:
    filters = normalize_filters(
        {
            "ticker": "AAPL",
            "source_type": None,
            "document_type": "",
            "section_hint": "risk",
        }
    )

    assert filters == {"ticker": "AAPL", "section_hint": "risk"}


def test_search_filters_reject_unknown_keys() -> None:
    with pytest.raises(RetrievalFilterError):
        normalize_filters({"unknown": "value"})


def test_apply_filters_matches_metadata_records() -> None:
    records = [
        {"ticker": "AAPL", "source_type": "sec"},
        {"ticker": "QAN", "source_type": "asx"},
    ]

    filtered = apply_filters(records, {"ticker": "AAPL"})

    assert filtered == [{"ticker": "AAPL", "source_type": "sec"}]
