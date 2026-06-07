"""Test sinh báo cáo weekly EBM."""
from app.reports.weekly_ebm import build_weekly_data, render_markdown
from app.services.pipeline import run_pipeline


def test_weekly_report_contains_required_sections():
    run_pipeline(max_results_per_query=10)
    data = build_weekly_data()
    md = render_markdown(data)
    for section in ["Tóm tắt điều hành", "Checklist thay đổi",
                    "An toàn thuốc", "Chưa nên thay đổi thực hành",
                    "Tài liệu tham khảo"]:
        assert section in md, f"Thiếu mục: {section}"


def test_report_separates_not_actionable():
    run_pipeline(max_results_per_query=10)
    data = build_weekly_data()
    # Phải có cơ chế đánh dấu "chưa đủ để thay đổi thực hành"
    assert "not_yet_change" in data
    assert isinstance(data["not_yet_change"], list)
