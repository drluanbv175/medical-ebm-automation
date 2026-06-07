"""Test cơ chế 'mới tuần này': watermark, đánh dấu mới, idempotent, bản tin cảnh báo."""
from app.database import session_scope
from app.models import EvidenceItem
from app.reports.alert_digest import build_alert_data, render_alert_markdown
from app.services import run_state
from app.services.pipeline import run_pipeline


def test_run_recorded_and_watermark():
    run_pipeline(max_results_per_query=10)
    last = run_state.last_finished_run()
    assert last is not None
    assert last.status == "ok"
    assert last.id in run_state.recent_run_ids(days=7)


def test_first_seen_set_on_insert():
    run_pipeline(max_results_per_query=10)
    with session_scope() as s:
        prim = s.query(EvidenceItem).filter(
            EvidenceItem.is_primary_record.is_(True)).all()
        # Mọi record chính phải có first_seen_run_id (nguồn gốc "mới")
        assert all(r.first_seen_run_id is not None for r in prim)


def test_new_detection_is_idempotent():
    """Chạy hai lần liên tiếp: lần sau KHÔNG có gì 'mới' và không thêm hàng."""
    run_pipeline(max_results_per_query=10)
    with session_scope() as s:
        count_before = s.query(EvidenceItem).count()
    stats2 = run_pipeline(max_results_per_query=10)
    with session_scope() as s:
        count_after = s.query(EvidenceItem).count()
    assert stats2["new_items"] == 0, "Lần chạy lặp lại không được tạo mục 'mới'"
    assert count_after == count_before, "Không được thêm hàng khi dữ liệu không đổi"


def test_alert_digest_reports_new():
    run_pipeline(max_results_per_query=10)
    data = build_alert_data(days=7)
    assert data["total_new"] >= 1
    md = render_alert_markdown(data)
    assert "Mới trong" in md
    # Phải có mục guideline hoặc actionable trong bản tin
    assert "Guideline" in md or "actionable" in md.lower()


def test_alert_digest_empty_when_no_recent():
    # Bản tin với cửa sổ 0 ngày -> không có run nào -> 'không có cập nhật mới'
    data = build_alert_data(days=0)
    md = render_alert_markdown(data)
    if data["total_new"] == 0:
        assert "Không có cập nhật mới" in md
