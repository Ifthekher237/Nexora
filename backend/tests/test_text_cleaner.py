from backend.app.services.processing.text_cleaner import clean_text


def test_clean_text_removes_excessive_whitespace() -> None:
    raw = "Revenue   increased\t\tby  12%\n\n\n\nDebt remained stable."

    cleaned = clean_text(raw)

    assert "   " not in cleaned
    assert "\n\n\n" not in cleaned
    assert "Revenue increased by 12%" in cleaned


def test_clean_text_preserves_financial_symbols_and_numbers() -> None:
    raw = "Free cash flow was $12.5m, margin 18%, debt-to-equity 0.42x."

    cleaned = clean_text(raw)

    assert "$12.5m" in cleaned
    assert "18%" in cleaned
    assert "0.42x" in cleaned
