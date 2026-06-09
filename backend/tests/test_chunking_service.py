from backend.app.services.processing.chunking_service import create_chunks


def _metadata() -> dict[str, str]:
    return {
        "company_name": "Apple Inc.",
        "ticker": "AAPL",
        "market": "US",
        "document_type": "sec_filing_metadata",
        "source_type": "sec",
        "published_at": "2026-05-29",
        "period": "2026",
    }


def test_short_text_becomes_one_chunk() -> None:
    chunks = create_chunks(
        "Revenue grew and risk remained manageable.",
        "PROC_TEST",
        "SRC_TEST",
        _metadata(),
    )

    assert len(chunks) == 1
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["ticker"] == "AAPL"


def test_chunking_creates_overlap() -> None:
    text = " ".join(f"word{i}" for i in range(760))

    chunks = create_chunks(text, "PROC_LONG", "SRC_LONG", _metadata())

    assert len(chunks) >= 3
    first_words = chunks[0]["chunk_text"].split()
    second_words = chunks[1]["chunk_text"].split()
    assert first_words[-60:] == second_words[:60]
