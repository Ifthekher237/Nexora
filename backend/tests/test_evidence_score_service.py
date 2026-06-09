from backend.app.services.risk.evidence_score_service import score_evidence_strength


def _reasoning(scores: list[float]) -> dict[str, object]:
    return {
        "evidence_map": [
            {"score": score, "source_document_id": f"doc-{index}", "source_number": f"Source {index + 1}"}
            for index, score in enumerate(scores)
        ],
        "causal_chain": [
            {"supporting_sources": ["Source 1"]},
            {"supporting_sources": ["Source 2"]},
        ],
    }


def test_evidence_score_increases_with_stronger_evidence() -> None:
    weak = score_evidence_strength(_reasoning([0.2]))
    strong = score_evidence_strength(_reasoning([0.8, 0.75, 0.7, 0.65]))

    assert strong["evidence_strength_score"] > weak["evidence_strength_score"]
    assert strong["evidence_summary"]["unique_documents"] > weak["evidence_summary"]["unique_documents"]
