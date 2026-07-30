"""Hồi quy G9-F5 (audit toàn diện G0-G10, 2026-07-30, MEDIUM):

g9_quality_gate.py::evaluate_study()'s G9-AUTO-02 trước vá này đọc
checkpoint["guardrail"] — giá trị ĐÓNG BĂNG tại thời điểm run_g9_auto.py
sinh artifact — dù file A10 thật (G9_A10_AUTHOR_INTEGRITY_<study>.md) có
thể đọc lại FRESH từ đĩa ngay tại đây. Cùng lớp "tin cache cũ" đã đóng ở
G4/G7/G8-AUTO-00 trong phiên audit này.

Đồng thời: run_g9_auto.py::guardrail_check_g9() R5 (đếm "[CẦN" ≥15) XUNG
ĐỘT TRỰC TIẾP với g9_quality_gate.py::_documents_clean() (dùng cho
G9-AUTO-05) — hàm đó đòi CHÍNH file A10 KHÔNG còn "[CẦN..." nào mới coi là
"sạch, sẵn sàng nộp". Một gói G9 THỰC SỰ hoàn chỉnh (can_count=0) khiến R5
cũ luôn ERROR đúng lúc gói đã sẵn sàng nhất — cùng lớp "phạt chính việc
hoàn thiện" đã sửa ở G8 R6. Hạ xuống cảnh báo thông tin."""

from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import g9_quality_gate as G9Q  # noqa: E402
import run_g9_auto as G9  # noqa: E402


def _row(report, criterion_id):
    for row in report["automatic_criteria"]:
        if row["id"] == criterion_id:
            return row
    raise AssertionError(f"Không tìm thấy tiêu chí {criterion_id}")


class TestGuardrailR5NoLongerBlocksOnFullyFilledPackage:
    def test_zero_can_labels_no_longer_errors(self):
        artifact = (
            "DRAFT DRAFT DRAFT CHỜ CHỜ\n"
            "PHẦN 1 PHẦN 2 PHẦN 3 PHẦN 4 PHẦN 5 PHẦN 6 PHẦN 7 PHẦN 8\n"
            "Cần bác sĩ kiểm chứng.\n"
        )
        result = G9.guardrail_check_g9(artifact)
        assert not any(e.startswith("R5") for e in result["errors"])
        assert result["passed"] is True

    def test_many_can_labels_also_does_not_error(self):
        artifact = (
            "DRAFT DRAFT DRAFT CHỜ CHỜ\n"
            "PHẦN 1 PHẦN 2 PHẦN 3 PHẦN 4 PHẦN 5 PHẦN 6 PHẦN 7 PHẦN 8\n"
            + "[CẦN] " * 20
            + "\nCần bác sĩ kiểm chứng.\n"
        )
        result = G9.guardrail_check_g9(artifact)
        assert not any(e.startswith("R5") for e in result["errors"])


class TestG9Auto02RefreshesGuardrailInsteadOfTrustingStaleCache:
    _CLEAN_A10 = (
        "DRAFT DRAFT DRAFT CHỜ CHỜ\n"
        "PHẦN 1 PHẦN 2 PHẦN 3 PHẦN 4 PHẦN 5 PHẦN 6 PHẦN 7 PHẦN 8\n"
        "Cần bác sĩ kiểm chứng.\n"
    )

    def test_stale_cached_pass_but_fresh_content_has_pii_is_now_caught(self, tmp_path):
        study = "PYTEST-G9-STALE-T1"
        out_dir = tmp_path / "exports" / study
        out_dir.mkdir(parents=True)
        (out_dir / f"G9_A10_AUTHOR_INTEGRITY_{study}.md").write_text(
            self._CLEAN_A10 + "\nCCCD 012345678901 phát hiện.\n", encoding="utf-8"
        )
        import json
        (out_dir / G9Q.CHECKPOINT_JSON).write_text(json.dumps({
            "gate": "G9", "study": study,
            "quality_contract_version": G9Q.QUALITY_CONTRACT_VERSION,
            "guardrail": {"passed": True, "errors": [], "warnings": []},
        }), encoding="utf-8")
        (out_dir / G9Q.READINESS_JSON).write_text(json.dumps({
            "schema_version": G9Q.QUALITY_CONTRACT_VERSION, "study": study,
            "disclaimer": "Cần bác sĩ kiểm chứng.",
        }), encoding="utf-8")
        report = G9Q.evaluate_study(study, out_dir, repo_root=tmp_path, write=False)
        row = _row(report, "G9-AUTO-02")
        assert row["status"] == "BLOCK"

    def test_stale_cached_block_but_fresh_content_now_clean_is_recognized(self, tmp_path):
        study = "PYTEST-G9-STALE-T2"
        out_dir = tmp_path / "exports" / study
        out_dir.mkdir(parents=True)
        (out_dir / f"G9_A10_AUTHOR_INTEGRITY_{study}.md").write_text(
            self._CLEAN_A10, encoding="utf-8"
        )
        import json
        (out_dir / G9Q.CHECKPOINT_JSON).write_text(json.dumps({
            "gate": "G9", "study": study,
            "quality_contract_version": G9Q.QUALITY_CONTRACT_VERSION,
            "guardrail": {"passed": False, "errors": ["R1 lỗi cũ"], "warnings": []},
        }), encoding="utf-8")
        (out_dir / G9Q.READINESS_JSON).write_text(json.dumps({
            "schema_version": G9Q.QUALITY_CONTRACT_VERSION, "study": study,
            "disclaimer": "Cần bác sĩ kiểm chứng.",
        }), encoding="utf-8")
        report = G9Q.evaluate_study(study, out_dir, repo_root=tmp_path, write=False)
        row = _row(report, "G9-AUTO-02")
        assert row["status"] == "PASS"
