"""Liêm chính danh mục thang điểm (task 1.3 + 1.4).

1.3 — seed_verified_scores() phải ghi ChangeLogEntry khi NÂNG CẤP một thang
      từ skeleton → verified, và KHÔNG ghi trùng khi chạy lại (idempotent).
1.4 — số liệu danh mục phải khớp doc RA_SOAT_THANG_DIEM_2026-06.md:
      32 verified, 16 needs_verification; không thang needs_verification nào có công thức.

Lưu ý: DB test là session-scoped (dùng chung). Các test ở đây viết theo tính
chất BẤT BIẾN nên không phụ thuộc thứ tự chạy.
"""
from __future__ import annotations

from app.clinical_scores import VERIFIED_SCORES, seed_clinical_scores, seed_verified_scores
from app.database import session_scope
from app.models import ChangeLogEntry, ClinicalScore

EXPECTED_VERIFIED = 32          # = len(VERIFIED_SCORES), doc 2026-06
EXPECTED_NEEDS_VERIFICATION = 16  # doc 2026-06: 16 công cụ chưa điền công thức


def _seed_all() -> None:
    """Seed idempotent để đảm bảo trạng thái nền, không phụ thuộc test khác."""
    seed_clinical_scores()
    seed_verified_scores()


def _changelog_count() -> int:
    with session_scope() as s:
        return s.query(ChangeLogEntry).filter_by(
            created_by="seed_verified_scores").count()


# ---- 1.4: liêm chính số liệu ----

def test_verified_scores_list_count_pinned():
    # Pin số lượng để mọi thêm/bớt thang verified là CHỦ Ý (khớp doc = 32)
    assert len(VERIFIED_SCORES) == EXPECTED_VERIFIED


def test_db_counts_match_doc():
    _seed_all()
    with session_scope() as s:
        verified = s.query(ClinicalScore).filter_by(update_status="verified").count()
        needs = s.query(ClinicalScore).filter_by(
            update_status="needs_verification").count()
    assert verified == EXPECTED_VERIFIED, f"verified={verified}, doc nói {EXPECTED_VERIFIED}"
    assert needs == EXPECTED_NEEDS_VERIFICATION, (
        f"needs_verification={needs}, doc nói {EXPECTED_NEEDS_VERIFICATION}")


def test_needs_verification_have_no_fabricated_formula():
    # Chống bịa: thang chưa xác minh KHÔNG được có công thức
    _seed_all()
    with session_scope() as s:
        for c in s.query(ClinicalScore).filter_by(
                update_status="needs_verification").all():
            assert c.calculation_method is None, f"{c.score_id} bịa công thức"


# ---- 1.3: change log khi nâng cấp ----

def test_reseed_does_not_duplicate_changelog():
    # Idempotent: chạy lại seed_verified_scores khi đã verified → không thêm log
    _seed_all()
    before = _changelog_count()
    seed_verified_scores()
    after = _changelog_count()
    assert after == before, f"ghi trùng change log: {before} -> {after}"


def test_upgrade_writes_changelog_entry():
    # Hạ 1 thang xuống needs_verification rồi seed lại → phải sinh đúng 1 log mới
    _seed_all()
    target = "fib4"
    with session_scope() as s:
        obj = s.query(ClinicalScore).filter_by(score_id=target).first()
        assert obj is not None, f"không có {target} để kiểm tra"
        obj.update_status = "needs_verification"
    before = _changelog_count()
    seed_verified_scores()
    after = _changelog_count()
    assert after == before + 1, f"nâng cấp không sinh change log: {before} -> {after}"
    with session_scope() as s:
        obj = s.query(ClinicalScore).filter_by(score_id=target).first()
        assert obj.update_status == "verified", f"{target} chưa trở lại verified"
