"""Test module nghiên cứu: dossier, checklist, gợi ý thống kê."""
from app.research import add_project
from app.research.checklists import (ACCEPTANCE_CHECKLIST, ETHICS_SUBMISSION_CHECKLIST,
                                     stats_suggestions, variable_framework)
from app.research.dossier import build_dossier_markdown


def test_stats_suggestions_by_design():
    assert any("ITT" in s for s in stats_suggestions("Thử nghiệm RCT đa trung tâm"))
    assert any("Cox" in s or "Kaplan" in s for s in stats_suggestions("cohort tiến cứu"))
    assert any("OR" in s for s in stats_suggestions("case-control"))
    # mặc định mô tả
    assert stats_suggestions(None)


def test_variable_framework_has_groups():
    vf = variable_framework()
    assert "Biến phụ thuộc / kết cục" in vf
    assert "Biến gây nhiễu (confounders)" in vf


def test_checklists_nonempty():
    assert len(ETHICS_SUBMISSION_CHECKLIST) >= 8
    assert len(ACCEPTANCE_CHECKLIST) >= 6


def test_build_dossier_contains_all_sections():
    add_project({
        "project_id": "RES-TEST-001",
        "project_title": "Hiệu quả SGLT2i trên bệnh thận mạn ngoại trú",
        "study_design": "Cohort tiến cứu",
        "primary_objective": "Đánh giá tiến triển CKD",
    })
    md = build_dossier_markdown("RES-TEST-001")
    assert md is not None
    for section in ["Đề cương rút gọn", "Tài liệu nền", "Gợi ý biến số",
                    "Gợi ý phân tích thống kê", "hội đồng đạo đức",
                    "Checklist nghiệm thu", "Tài liệu tham khảo"]:
        assert section in md, f"Thiếu mục: {section}"


def test_dossier_missing_project_returns_none():
    assert build_dossier_markdown("KHONG-TON-TAI") is None
