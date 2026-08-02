"""Hồi quy G4-F2/F3 (audit toàn diện G0-G10, 2026-07-30, HIGH):

g4_quality_gate.py::evaluate_g4_quality()'s G4-AUTO-00 trước vá này đọc
checkpoint["guardrail"] — giá trị ĐÓNG BĂNG tại thời điểm run_g4_auto.py
sinh artifact — dù artifact_text được đọc FRESH từ đĩa ngay bên cạnh (tham
số hàm). Rà lại tools/run_g4_auto.py::guardrail() cho thấy R3 (chống tự
công bố "đã khóa/đã duyệt SAP") đã là một luật THẬT (kiểm theo dòng, phân
biệt câu điều kiện/quy trình với công bố thật) — không phải tautology đơn
giản như 3 luật còn lại (R4/R6/R7, vẫn kiểm boilerplate luôn in cứng) —
nhưng guardrail() chỉ được gọi ĐÚNG MỘT LẦN ngay sau khi sinh (main() của
run_g4_auto.py), không ai gọi lại nó trên artifact_text SAU KHI bác sĩ (hay
bất kỳ ai có quyền sửa file) chỉnh sửa. Cùng lớp lỗi "tin cache cũ" đã đóng
ở G7-AUTO-00/G8-AUTO-00 trong phiên audit này — nay G4-AUTO-00 chạy lại
guardrail() trên artifact_text thật."""

from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import g4_quality_gate as G4Q  # noqa: E402

from tests.test_g4_quality_gate import (  # noqa: E402
    _filled_comparative_sap,
    _g3_checkpoint,
    _meta,
)


def _evaluate_minimal(checkpoint, artifact_text):
    return G4Q.evaluate_g4_quality(
        study="TEST-STALE",
        checkpoint=checkpoint,
        artifact_text=artifact_text,
        g3_checkpoint=_g3_checkpoint(),
        g1_checkpoint={"design": {"internal_code": "rct"}},
        meta=_meta(),
        ledger_signed=False,
        ledger_reason="chưa ai duyệt",
        signature_scope=None,
        role_key_available=False,
        cross_gate_refs={},
    )


def _row(report, criterion_id):
    for row in report["automatic_criteria"] + report["approval_criteria"]:
        if row["id"] == criterion_id:
            return row
    raise AssertionError(f"Không tìm thấy tiêu chí {criterion_id}")


class TestG4Auto00RefreshesGuardrailInsteadOfTrustingStaleCache:
    def test_stale_cached_pass_but_fresh_content_self_claims_approval_is_now_caught(self):
        """checkpoint["guardrail"]="✅ PASS" (cache CŨ) nhưng artifact_text
        HIỆN TẠI trên đĩa đã bị sửa để tự công bố đã duyệt — G4-AUTO-00 phải
        BLOCK vì đọc lại bản thật, không tin cache."""
        checkpoint = {"gate": "G4", "study": "TEST-STALE", "design_code": "rct",
                      "guardrail": "✅ PASS"}
        tampered = _filled_comparative_sap() + "\nNghiên cứu đã được duyệt hoàn toàn.\n"
        report = _evaluate_minimal(checkpoint, tampered)
        assert _row(report, "G4-AUTO-00")["status"] == "BLOCK"

    def test_stale_cached_block_but_fresh_content_now_clean_is_recognized(self):
        """Ngược lại: cache CŨ ghi lỗi (vd "⚠ 2 LỖI") nhưng bác sĩ đã sửa file
        trên đĩa cho sạch — G4-AUTO-00 phải PASS vì đọc lại bản thật, không
        tiếp tục chặn oan theo cache cũ."""
        checkpoint = {"gate": "G4", "study": "TEST-STALE-FIXED", "design_code": "rct",
                      "guardrail": "⚠ 2 LỖI"}
        report = _evaluate_minimal(checkpoint, _filled_comparative_sap())
        assert _row(report, "G4-AUTO-00")["status"] == "PASS"
