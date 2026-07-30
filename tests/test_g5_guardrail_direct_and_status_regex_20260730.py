"""Hồi quy G5-F2/F4/F5 (audit toàn diện G0-G10, 2026-07-30):

G5-F2 (HIGH): guardrail() R1/R4/R5/R7 trong run_g5_auto.py kiểm chuỗi mà
generate_artifact() luôn in cứng vô điều kiện — không thể fail với BẤT KỲ
artifact thật nào. Chỉ R2 (PII)/R3 (vượt cổng)/R6 (tự gán GRADE) thật sự
phản ứng với nội dung. Đã thêm chú thích trung thực về phạm vi; test dưới
đây xác nhận cả hai vế: (a) R2/R3/R6 CÓ THỂ fail với nội dung xấu — vế mà
trước đây KHÔNG test nào xác nhận (G5-F4: grep '.guardrail(' trong
tests/*.py trước vá này rỗng); (b) artifact THẬT (không phải fixture tay)
luôn qua được R1/R4/R5/R7 — đúng bản chất cấu trúc đã ghi nhận, không phải
lỗi mới.

G5-F5 (LOW): _status_is_locked() ở lock_analysis_dataset.py/g5_quality_
gate.py trước đây chỉ nhận "CHƯA/KHÔNG" có dấu, lệch với bản chấp nhận cả
không dấu ở run_g5_auto.py — đã đồng bộ cả 3 nơi."""

from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import g5_quality_gate as G5Q  # noqa: E402
import lock_analysis_dataset as LAD  # noqa: E402
import run_g5_auto as G5  # noqa: E402


def _real_artifact(design_code: str = "cohort") -> str:
    rows, specialty = G5.build_redcap_rows(design_code, "Test topic")
    return G5.generate_artifact(
        "TEST-STUDY", "Test topic", design_code,
        100, 120, 60, "2026-07-30", rows, specialty,
    )


class TestGuardrailContentSensitiveRulesCanActuallyFail:
    """G5-F4: trước vá này KHÔNG test nào gọi guardrail() trực tiếp."""

    def test_r2_fails_on_real_pii_pattern(self):
        artifact = _real_artifact() + "\nCCCD 012345678901 của người tham gia.\n"
        errors, _warnings = G5.guardrail(artifact)
        assert any(e.startswith("R2") for e in errors)

    def test_r3_fails_on_gate_ab_overreach(self):
        artifact = _real_artifact() + "\nĐã áp dụng cho Cổng A của bệnh nhân này.\n"
        errors, _warnings = G5.guardrail(artifact)
        assert any(e.startswith("R3") for e in errors)

    def test_r6_fails_on_self_assigned_grade(self):
        artifact = _real_artifact() + "\nMức độ khuyến cáo: A cho can thiệp này.\n"
        errors, _warnings = G5.guardrail(artifact)
        assert any(e.startswith("R6") for e in errors)

    def test_clean_real_artifact_passes_all_seven(self):
        errors, _warnings = G5.guardrail(_real_artifact())
        assert errors == []


class TestGuardrailStructuralRulesDocumentedLimitation:
    """R1/R4/R5/R7 kiểm boilerplate luôn in cứng — xác nhận (không phải sửa)
    rằng MỌI artifact thật generate_artifact() sinh ra đều qua được 4 luật
    này, đúng bản chất "structural-only" đã ghi nhận trong guardrail()."""

    def test_every_design_code_passes_r1_r4_r5_r7(self):
        for design in ("rct", "cohort", "case_control", "cross_sectional",
                       "diagnostic", "sr_ma", "prediction", "qualitative"):
            errors, _warnings = G5.guardrail(_real_artifact(design))
            structural_errors = [
                e for e in errors if e.startswith(("R1", "R4", "R5", "R7"))
            ]
            assert not structural_errors, f"{design}: {structural_errors}"


class TestStatusIsLockedRegexConsistentAcrossThreeModules:
    """G5-F5: 3 hàm _status_is_locked() (run_g5_auto.py dùng regex inline,
    lock_analysis_dataset.py, g5_quality_gate.py) phải kết luận GIỐNG NHAU
    cho cùng một chuỗi trạng thái, kể cả biến thể không dấu.

    Rủi ro thực tế THẤP (đúng như audit ghi nhận): vì điều kiện phụ vẫn đòi
    chuỗi bắt đầu bằng "LOCKED", một phủ định không dấu đứng MỘT MÌNH (vd
    "KHONG LOCKED") vẫn bị coi là chưa khóa ở CẢ 2 phiên bản regex — chỉ khác
    khi chuỗi bắt đầu bằng "LOCKED" thật nhưng có cụm phủ định không dấu xuất
    hiện sau đó (kịch bản hiếm nhưng có thể xảy ra nếu một nơi khác ghép
    chuỗi trạng thái không đúng chuẩn)."""

    def test_locked_prefix_with_later_non_diacritic_negation_now_caught(self):
        value = "LOCKED nhung du lieu con CHUA LOCKED that su o may phu"
        assert LAD._status_is_locked(value) is False
        assert G5Q._status_is_locked(value) is False

    def test_real_locked_value_still_recognized(self):
        value = "LOCKED — 2026-07-30"
        assert LAD._status_is_locked(value) is True
        assert G5Q._status_is_locked(value) is True
