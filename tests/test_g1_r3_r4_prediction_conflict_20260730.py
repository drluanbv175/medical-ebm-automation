"""Hồi quy (audit toàn diện G0-G10, 2026-07-30) — 3 phát hiện HIGH trong G1:

G1-F1: guardrail R3 (chống tự ghi G4=LOCKED) kiểm chuỗi SAI ĐỊNH DẠNG
("G4_STATUS = LOCKED" có dấu cách, hoặc "G4=LOCKED") — chính template luôn
in KHÔNG dấu cách "G4_STATUS=LOCKED | ... | G4_LOCK_DATE=[date]" như một
HƯỚNG DẪN (vô hại, placeholder chưa điền), nên R3 trước vá này KHÔNG BAO GIỜ
có thể fail dù văn bản có bị sửa để tự nhận G4 đã khóa.

G1-F2: guardrail R4 (chống bịa effect size) kiểm "[CẦN" trên TOÀN VĂN BẢN —
template luôn có ≥40 chỗ [CẦN] không liên quan effect size nên R4 trước vá
này luôn PASS bất kể một OR/RR/HR/MD cụ thể bị bịa ở nơi khác trong văn bản.

G1-F3: tools/g1_quality_gate.py::evaluate_g1_quality() — dict conflict_patterns
dùng cho G1-AUTO-04c ("SAP không chứa khuôn phân tích mâu thuẫn với thiết
kế") trước vá này HOÀN TOÀN THIẾU key 'prediction' — đúng thiết kế có lịch
sử rơi vào khuôn sr_ma nhiều lần (xem docstring g1_design_blocks.py và
nhánh `elif internal == "prediction"` ở run_g1_auto.py, thêm riêng
2026-07-21 vì trước đó rơi vào else viết cho sr_ma)."""

from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import g1_quality_gate as G1Q  # noqa: E402
import run_g1_auto as G1  # noqa: E402


class TestGuardrailR3RealClaimVsInstructionalTemplate:
    """R3 phải phân biệt HƯỚNG DẪN mẫu (luôn có mặt, vô hại) với việc văn
    bản đã bị sửa để tự nhận G4 đã khóa (nghi vượt cổng)."""

    def test_fresh_template_with_unfilled_date_placeholder_not_flagged(self):
        artifact = (
            "**→ Để mở G4:** Bác sĩ xác nhận \"SAP đã khóa ngày [DD/MM/YYYY]\"\n"
            "  Agent ghi: G4_STATUS=LOCKED | G4_SAP_VERSION=1.0 | G4_LOCK_DATE=[date]\n"
        )
        result = G1.guardrail_check_g1(artifact, effects=[], topic="", internal_code="")
        assert not any("R3" in e for e in result["errors"])
        assert any("R3" in w for w in result["warnings"])

    def test_lock_date_placeholder_replaced_with_real_date_is_flagged(self):
        artifact = (
            "**→ Để mở G4:** Bác sĩ xác nhận \"SAP đã khóa ngày 30/07/2026\"\n"
            "  Agent ghi: G4_STATUS=LOCKED | G4_SAP_VERSION=1.0 | G4_LOCK_DATE=30/07/2026\n"
        )
        result = G1.guardrail_check_g1(artifact, effects=[], topic="", internal_code="")
        assert any("R3" in e for e in result["errors"])

    def test_direct_short_form_claim_is_flagged(self):
        artifact = "Trạng thái: G4=LOCKED (đã xong hết).\n"
        result = G1.guardrail_check_g1(artifact, effects=[], topic="", internal_code="")
        assert any("R3" in e for e in result["errors"])


class TestGuardrailR4LocalizedEffectSizeCheck:
    """R4 phải kiểm CỤC BỘ quanh mỗi effect size cụ thể (OR/RR/HR/MD=N),
    không phải sự tồn tại của '[CẦN' bất kỳ đâu trong toàn văn bản."""

    def test_effect_size_with_pmid_nearby_not_flagged(self):
        artifact = (
            "Nội dung SAP dài...\n"
            "  • RR = 0.80 (95%CI: 0.65–0.98) — PMID:12345678 (2024) Bài mẫu\n"
            "Hết.\n"
        )
        result = G1.guardrail_check_g1(artifact, effects=[], topic="", internal_code="")
        assert not any("R4" in e for e in result["errors"])
        assert any("R4" in w for w in result["warnings"])

    def test_effect_size_with_can_label_nearby_not_flagged(self):
        artifact = (
            "Nội dung SAP dài...\n"
            "  Cỡ hiệu ứng ước tính: OR = 1.50 [CẦN xác nhận qua y văn]\n"
            "Hết.\n"
        )
        result = G1.guardrail_check_g1(artifact, effects=[], topic="", internal_code="")
        assert not any("R4" in e for e in result["errors"])

    def test_effect_size_without_source_or_label_anywhere_nearby_is_flagged(self):
        # Văn bản CÓ nhãn [CẦN] ở đâu đó khác — đúng lỗi cũ khiến R4 luôn PASS —
        # nhưng KHÔNG có gần chỗ effect size cụ thể này.
        artifact = (
            "PHẦN KHÁC: [CẦN bác sĩ điền tên đơn vị]\n"
            + ("." * 200) +
            "\n  Hiệu quả ước tính: OR = 2.30, có ý nghĩa thống kê.\n"
            + ("." * 200) +
            "\nHết. Cần bác sĩ kiểm chứng.\n"
        )
        result = G1.guardrail_check_g1(artifact, effects=[], topic="", internal_code="")
        assert any("R4" in e for e in result["errors"])

    def test_no_effect_size_pattern_at_all_passes(self):
        artifact = "SAP chưa có effect size nào được điền. Cần bác sĩ kiểm chứng.\n"
        result = G1.guardrail_check_g1(artifact, effects=[], topic="", internal_code="")
        assert not any("R4" in e for e in result["errors"])


class TestG1Auto04cCoversPredictionDesign:
    """conflict_patterns['prediction'] trước vá này không tồn tại — bất kỳ
    nội dung SAP nào (kể cả khuôn sr_ma rò vào) đều PASS oan cho thiết kế
    'prediction'."""

    def test_conflict_patterns_dict_has_prediction_key(self):
        design = G1.infer_study_design(
            "treatment", {"n_sr": 0, "n_rct": 0},
            "Phát triển mô hình dự đoán nguy cơ tái nhập viện ở bệnh nhân suy tim",
        )
        assert design["internal_code"] == "prediction"

        report = G1Q.evaluate_g1_quality(
            design=design,
            artifact_texts={"A2": "SAP bình thường không có khuôn sai.\nHartung-Knapp\n"},
            artifact_paths={},
            g0_checkpoint={"topic": "x"},
            meta={},
            evidence_identifiers={},
            guardrail_passed=True,
        )
        consistency = next(
            row for row in report["automatic_criteria"]
            if row["id"] == "G1-AUTO-04c"
        )
        assert consistency["status"] == "BLOCK"

    def test_clean_prediction_sap_not_blocked_by_04c(self):
        design = G1.infer_study_design(
            "treatment", {"n_sr": 0, "n_rct": 0},
            "Phát triển mô hình dự đoán nguy cơ tái nhập viện ở bệnh nhân suy tim",
        )
        report = G1Q.evaluate_g1_quality(
            design=design,
            artifact_texts={"A2": "SAP dùng logistic/Cox + shrinkage + calibration, không có khuôn sai.\n"},
            artifact_paths={},
            g0_checkpoint={"topic": "x"},
            meta={},
            evidence_identifiers={},
            guardrail_passed=True,
        )
        consistency = next(
            row for row in report["automatic_criteria"]
            if row["id"] == "G1-AUTO-04c"
        )
        assert consistency["status"] == "PASS"

    def test_real_generated_prediction_artifact_never_trips_its_own_new_conflict_markers(self):
        """Tránh 'tautology ngược' (G10-02): 2 cụm mới thêm cho 'prediction'
        không được xuất hiện trong chính artifact THẬT do generate_g1_artifact()
        sinh ra cho thiết kế này — nếu không, mọi đề tài prediction hợp lệ sẽ
        tự BLOCK oan."""
        design = G1.infer_study_design(
            "treatment", {"n_sr": 0, "n_rct": 0},
            "Phát triển mô hình dự đoán nguy cơ tái nhập viện ở bệnh nhân suy tim",
        )
        assert design["internal_code"] == "prediction"
        artifact = G1.generate_g1_artifact(
            "Phát triển mô hình dự đoán nguy cơ tái nhập viện ở bệnh nhân suy tim",
            "METHOD-CHECK-PREDICTION",
            design["resolved_question_type"],
            design,
            [],
            {},
            "2026-07-30 10:00",
            meta={},
        )
        assert "Hartung-Knapp" not in artifact
        assert "funnel plot/Egger" not in artifact
