"""Hồi quy phát hiện #2 (Medium) của Workflow đối kháng đa-agent 2026-09-05
(vòng 16) trong app/research/checklists.py::stats_suggestions().

CƠ CHẾ LỖI: hàm dừng ở match ĐẦU TIÊN theo THỨ TỰ KHAI BÁO của
`_STATS_BY_DESIGN`. Một thiết kế "nested case-control" (bệnh-chứng lồng
trong một cohort có sẵn — phổ biến trong dịch tễ học) chứa CẢ HAI từ khóa
"cohort"/"thuần tập" LẪN "case-control"/"bệnh chứng". Khi "cohort" được
khai báo TRƯỚC "case-control" trong dict, hàm trả nhầm gợi ý của cohort
(RR/Cox/Kaplan-Meier) cho một thiết kế thực ra cần gợi ý của case-control
(OR/hồi quy logistic/ghép cặp) — sai phương pháp thống kê được đề xuất.
Hàm này được app/research/dossier.py::build_dossier_markdown() gọi trực
tiếp (Mục 4 "Gợi ý phân tích thống kê" của hồ sơ nghiên cứu tự sinh).

BẢN VÁ: đặt thiết kế CỤ THỂ hơn (case-control, rct) TRƯỚC thiết kế TỔNG
QUÁT hơn (cross-sectional, cohort) trong khai báo dict, để khớp đúng ưu
tiên khi một chuỗi mô tả chứa nhiều từ khóa.

Nguyên tắc viết test: gọi THẲNG `stats_suggestions()` thật."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.research.checklists import stats_suggestions  # noqa: E402


class TestNestedCaseControlDuocGoiYDungCaseControlKhongPhaiCohort:
    """★★★ Ca chính — mô tả chứa CẢ hai từ khóa "cohort" và "case-control"
    phải trả gợi ý của case-control (đặc hiệu hơn), không phải cohort."""

    def test_case_control_long_trong_thuan_tap(self):
        items = stats_suggestions("Case-control lồng trong thuần tập (nested case-control)")
        assert any("OR" in s for s in items), (
            "TRƯỚC bản vá: 'cohort' được kiểm TRƯỚC 'case-control' trong dict "
            "nên hàm trả gợi ý cohort (RR/Cox) cho một thiết kế case-control thật"
        )
        assert not any("Kaplan" in s or "Cox" in s for s in items)

    def test_nested_case_control_trong_cohort_da_co(self):
        items = stats_suggestions("Nested case-control study trong cohort đã có")
        assert any("OR" in s for s in items)
        assert not any("Kaplan" in s or "Cox" in s for s in items)


class TestThietKeThuanTuyVanGiuHanhViCu:
    """Đối chứng bắt buộc — mô tả CHỈ chứa một loại từ khóa (không lồng
    ghép) vẫn nhận đúng gợi ý như hành vi gốc."""

    def test_case_control_thuan_tuy(self):
        items = stats_suggestions("case-control")
        assert any("OR" in s for s in items)

    def test_cohort_thuan_tuy(self):
        items = stats_suggestions("cohort tiến cứu")
        assert any("Cox" in s or "Kaplan" in s for s in items)

    def test_rct(self):
        items = stats_suggestions("Thử nghiệm RCT đa trung tâm")
        assert any("ITT" in s for s in items)

    def test_cross_sectional(self):
        items = stats_suggestions("Nghiên cứu cắt ngang mô tả")
        assert any("STROBE (cross-sectional)" in s for s in items)

    def test_none_tra_ve_descriptive(self):
        assert stats_suggestions(None)
        items = stats_suggestions(None)
        assert any("mô tả" in s.lower() for s in items)
