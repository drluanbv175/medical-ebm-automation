"""Test danh mục thang điểm + nâng cấp verified (có công thức + nguồn)."""
from app.clinical_scores import seed_clinical_scores, seed_verified_scores
from app.clinical_scores.verified import VERIFIED_SCORES
from app.database import session_scope
from app.models import ClinicalScore


def test_seed_then_verify():
    seed_clinical_scores()
    res = seed_verified_scores()
    assert res["updated"] + res["inserted"] >= len(VERIFIED_SCORES)
    with session_scope() as s:
        verified = s.query(ClinicalScore).filter_by(update_status="verified").all()
        assert len(verified) >= len(VERIFIED_SCORES)
        # Mọi công cụ verified phải có công thức + nguồn (chống bịa đặt)
        for c in verified:
            assert c.calculation_method, f"{c.score_name} thiếu công thức"
            assert c.source, f"{c.score_name} thiếu nguồn"


def test_unverified_have_no_fabricated_formula():
    seed_clinical_scores()
    with session_scope() as s:
        for c in s.query(ClinicalScore).filter_by(update_status="needs_verification").all():
            # Công cụ chưa xác minh KHÔNG được tự bịa công thức
            assert c.calculation_method is None
