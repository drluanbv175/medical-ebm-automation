"""Hồi quy G6-01/G6-03/G6-05 (audit toàn diện G0-G10, 2026-07-30):

G6-01 (CRITICAL): guardrail() của run_g6_auto.py — luật R6 (kiểm mật độ
95%CI trong artifact+scripts) trước vá này CẢ HAI nhánh if/else đều chỉ
warnings_list.append(...) — KHÔNG nhánh nào chạm errors, nên R6 về mặt CẤU
TRÚC không thể tạo lỗi bất kể ci_n bằng bao nhiêu (kể cả ci_n=0). Đây là lỗi
mã nguồn thật, khác các luật R4/R5/R7 (vốn chỉ yếu tín hiệu vì boilerplate
luôn in cứng, không phải lỗi cấu trúc). Sửa: nhánh else nay errors.append
thật khi thiếu hẳn yêu cầu 95%CI.

Trước vá này KHÔNG có test nào trong tests/*.py gọi guardrail() trực tiếp để
buộc một luật R phải fail (G6-05) — chỉ có 1 dòng docstring nhắc tên hàm.

G6-03 (HIGH): PHẦN 6 "TIÊU CHÍ QUA CỔNG G6" của artifact liệt kê 6 điều kiện
nhưng KHÔNG điều kiện nào phản ánh trạng thái thật — kể cả mục "G4 = LOCKED"
vốn CÓ SẴN biến `g4_locked` tính đúng ở đầu generate_artifact() (đã dùng thật
ở PHẦN 1) nhưng PHẦN 6 vẫn luôn in "- [ ]" tĩnh. 5 mục còn lại (chạy script/
Table 1/kết quả chính/sensitivity/bác sĩ duyệt) đòi hỏi hành động xảy ra SAU
khi artifact này sinh ra nên đúng chủ định vẫn giữ "[ ]" — không phải lỗi."""

from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import run_g6_auto as G6  # noqa: E402

_V = {
    "exposure": "phoi_nhiem",
    "outcome": "ket_cuc",
    "time_col": "thoi_gian",
    "covariates": ["tuoi", "gioi"],
    "all_vars": ["ma_bn", "tuoi", "gioi", "phoi_nhiem", "ket_cuc", "thoi_gian"],
    "detection_log": [],
}


def _full_scripts_text(design_code: str) -> str:
    r03 = G6.R_ANALYSIS_MAP_FUNC(design_code, _V, 100, 0.05, 0.8, 1.5, "RR")
    scripts = {
        "00_setup.R": G6.R_00_SETUP,
        "01_cleaning.R": G6.make_r01_cleaning(_V, design_code),
        "02_tables.R": G6.make_r02_tables(_V, design_code),
        "03_analysis.R": r03,
    }
    cli_code = G6.make_run_analysis_cli(_V, 100, "TEST-STUDY", design_code, "RR")
    sens_code = G6.make_sensitivity_analysis(_V, "TEST-STUDY", design_code)
    return "\n".join(scripts.values()) + cli_code + sens_code


def _artifact(design_code: str, g4_status: str = "LOCKED") -> str:
    return G6.generate_artifact(
        "TEST-STUDY", "Test topic", design_code, "CONSORT 2025",
        100, 0.05, 0.8, 1.5, "RR", g4_status, "2026-07-30", "scripts/", _V,
    )


class TestGuardrailR6CanActuallyFail:
    """G6-05: gọi guardrail() TRỰC TIẾP với input dựng sẵn để buộc R6 phải
    fail — trước vá này KHÔNG thể fail dù ci_n=0."""

    def test_r6_fails_when_no_ci_pattern_anywhere(self):
        artifact = "Nội dung A7 không có gì liên quan khoảng tin cậy.\nCần bác sĩ kiểm chứng.\n"
        errors, _warnings = G6.guardrail(artifact, "")
        assert any(e.startswith("R6") for e in errors), (
            "R6 phải fail khi ci_n=0 — trước vá này cả 2 nhánh chỉ warnings, không bao giờ fail"
        )

    def test_r6_passes_when_ci_pattern_present_enough(self):
        artifact = "95%CI 95%CI 95%CI đủ nhiều lần.\nCần bác sĩ kiểm chứng.\n"
        errors, _warnings = G6.guardrail(artifact, "")
        assert not any(e.startswith("R6") for e in errors)

    def test_real_generated_artifact_for_every_design_still_passes_r6(self):
        """Đóng vòng: fix không được làm sinh generation THẬT (không phải
        fixture tay) tự fail oan cho bất kỳ thiết kế nào trong 8 mã."""
        for design in ("rct", "cohort", "case_control", "cross_sectional",
                       "diagnostic", "sr_ma", "prediction", "qualitative"):
            artifact = _artifact(design)
            all_scripts_text = _full_scripts_text(design)
            errors, _warnings = G6.guardrail(artifact, all_scripts_text)
            r6_errors = [e for e in errors if e.startswith("R6")]
            assert not r6_errors, f"{design}: R6 fail oan trên artifact thật: {r6_errors}"


class TestPhan6ChecklistG4LockReflectsRealState:
    def test_g4_locked_shows_checked_box(self):
        artifact = _artifact("cohort", g4_status="LOCKED")
        phan6 = artifact.split("## PHẦN 6", 1)[1]
        assert "- [x] **G4 = LOCKED**" in phan6

    def test_g4_not_locked_shows_unchecked_box_with_can_label(self):
        artifact = _artifact("cohort", g4_status="PENDING")
        phan6 = artifact.split("## PHẦN 6", 1)[1]
        assert "- [ ] **G4 = LOCKED**" in phan6
        assert "[CẦN BÁC SĨ XÁC NHẬN]" in phan6

    def test_other_five_items_remain_unchecked_placeholders_by_design(self):
        """5 mục còn lại đòi hỏi hành động SAU khi artifact sinh (chạy
        script/xem dữ liệu/bác sĩ duyệt) — không nên tự đánh dấu, kể cả khi
        G4 đã khóa."""
        artifact = _artifact("cohort", g4_status="LOCKED")
        phan6 = artifact.split("## PHẦN 6", 1)[1]
        assert phan6.count("- [ ]") == 5
