"""Test pipeline + database insert/update + không mất dữ liệu cũ khi chạy lại."""
from app.database import session_scope
from app.models import ChangeLogEntry, EvidenceItem
from app.services.pipeline import run_pipeline


def test_pipeline_inserts_and_classifies():
    stats = run_pipeline(max_results_per_query=10)
    assert stats["total"] > 0
    with session_scope() as s:
        assert s.query(EvidenceItem).count() > 0
        # Phải có ít nhất 1 guideline được phân loại actionable hoặc need_full_text
        guidelines = s.query(EvidenceItem).filter(
            EvidenceItem.study_type == "guideline").all()
        assert guidelines


def test_rerun_does_not_lose_data():
    run_pipeline(max_results_per_query=10)
    with session_scope() as s:
        count1 = s.query(EvidenceItem).count()
    # Chạy lại: upsert, không xóa.
    run_pipeline(max_results_per_query=10)
    with session_scope() as s:
        count2 = s.query(EvidenceItem).count()
    assert count2 >= count1  # không mất dữ liệu


def test_changelog_written():
    run_pipeline(max_results_per_query=5)
    with session_scope() as s:
        assert s.query(ChangeLogEntry).count() > 0


def test_actionable_has_reason():
    run_pipeline(max_results_per_query=10)
    with session_scope() as s:
        for r in s.query(EvidenceItem).filter(EvidenceItem.is_actionable.is_(True)).all():
            assert r.actionable_reason, "Mỗi mục actionable phải có lý do"
