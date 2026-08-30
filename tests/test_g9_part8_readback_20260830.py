"""Hồi quy audit cổng 30/08/2026 (khoảng hở #5): cơ chế ĐỌC NGƯỢC tick ☐/☑
của checklist "Phần 8 — Hard Gate" trên A10 (tiêu chí G9-AUTO-08).

Trước bản vá, khoảng trống đã được chính g9_quality_gate.py tự khai ở chú
thích G9-HUMAN-11: tờ Phần 8 bác sĩ đọc/tích trên giấy/Word "tách rời khỏi
cổng máy-chấm thật... không có cơ chế đọc ngược trạng thái tick ☐/☑".

Hợp đồng của tiêu chí mới:
- Chỉ đếm ☑/☒/[x] — KHÔNG đếm ✅ (template tự in ✅ cho trạng thái cổng dẫn
  xuất; đếm nó là tự-dương-tính, cùng họ tautology đã vá ở G3/G8).
- ADVISORY-ONLY: REVIEW của G9-AUTO-08 không bao giờ đổi trạng thái cổng —
  gate hoá sẽ lật đề tài ĐÃ khóa và phạt người tích tờ sớm (bài học G8 R6).
- "File thiếu/đổi khuôn" (None) phải TÁCH khỏi "đọc được nhưng 0 tick" (BH08).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import g9_quality_gate as G9Q  # noqa: E402

from tests.test_g9_quality_gate import _evaluate_ready  # noqa: E402


def _row(report: dict, cid: str) -> dict:
    rows = [r for r in report["automatic_criteria"] if r["id"] == cid]
    assert rows, f"thiếu tiêu chí {cid} trong báo cáo"
    return rows[0]


class TestPart8TickStateParser:
    def test_missing_file_returns_none_not_zero(self, tmp_path: Path):
        found, ticked, unticked = G9Q._part8_tick_state(tmp_path / "khong-ton-tai.md")
        assert found is None and ticked == 0 and unticked == 0

    def test_file_without_part8_header_returns_none(self, tmp_path: Path):
        p = tmp_path / "a10.md"
        p.write_text("# A10\n☑ tick lạc ngoài mục\n", encoding="utf-8")
        assert G9Q._part8_tick_state(p)[0] is None

    def test_counts_tick_variants_but_not_template_checkmark(self, tmp_path: Path):
        p = tmp_path / "a10.md"
        p.write_text(
            "# A10\n"
            "nội dung phần trước ☑ không được đếm\n"
            "## Phần 8 — Tiêu chí Cổng G9 (Hard Gate)\n"
            "☑ Đã ký đầy đủ\n"
            "☒ Không cần\n"
            "[x] Đã kiểm chứng\n"
            "☐ Chưa nộp  ☐ Đã nộp\n"
            "| Trạng thái G2 | ✅ Có |\n",  # ✅ của template — cấm đếm
            encoding="utf-8",
        )
        found, ticked, unticked = G9Q._part8_tick_state(p)
        assert found is True
        assert ticked == 3, "phải đếm đúng ☑/☒/[x] trong mục Phần 8, không đếm ✅"
        assert unticked == 2


class TestPart8ConsistencyVerdict:
    """Đủ 4 nhánh của hàm thuần — gồm nhánh 'đã ký mà tờ trắng' vốn rất nặng
    nếu phải dựng chuỗi ký thật."""

    def test_unreadable_is_review_not_guess(self):
        status, evidence = G9Q._part8_consistency(None, 0, 0, False, False)
        assert status == "REVIEW" and "KHÔNG suy đoán" in evidence

    def test_paper_ticked_but_electronic_pending_is_review(self):
        status, evidence = G9Q._part8_consistency(True, 5, 3, True, False)
        assert status == "REVIEW" and "tờ giấy không phải cổng" in evidence

    def test_signed_but_paper_blank_is_review(self):
        status, evidence = G9Q._part8_consistency(True, 0, 12, False, True)
        assert status == "REVIEW" and "không còn khớp hồ sơ" in evidence

    def test_consistent_states_pass(self):
        # Đầu vòng đời: chưa tích, chưa ký, chưa pending gì đáng nói.
        assert G9Q._part8_consistency(True, 0, 12, False, False)[0] == "PASS"
        # Cuối vòng đời: đã tích, đã ký.
        assert G9Q._part8_consistency(True, 12, 0, False, True)[0] == "PASS"
        # Tích sớm khi hồ sơ điện tử cũng đã đủ (không pending): nhất quán.
        assert G9Q._part8_consistency(True, 12, 0, False, False)[0] == "PASS"


class TestAdvisoryOnlyIntegration:
    def test_ready_status_survives_part8_review(self, tmp_path, monkeypatch):
        """Đề tài đủ điều kiện READY: dù A10 fixture không có mục Phần 8
        (G9-AUTO-08 = REVIEW), trạng thái cổng KHÔNG được tụt — bằng chứng
        advisory-only, không hồi quy trạng thái các đề tài hiện có."""
        out_dir, report = _evaluate_ready(tmp_path, monkeypatch)
        row = _row(report, "G9-AUTO-08")
        a10 = out_dir / "G9_A10_AUTHOR_INTEGRITY_PYTEST-G9Q.md"
        has_part8 = bool(
            a10.exists() and G9Q._PART8_HEADER_RE.search(a10.read_text(encoding="utf-8"))
        )
        if has_part8:
            assert row["status"] == "PASS", row
        else:
            assert row["status"] == "REVIEW", row
        assert report["status"] == G9Q.STATUS_READY

    def test_paper_ahead_of_machine_flagged_without_changing_status(
        self, tmp_path, monkeypatch
    ):
        """Chiều lệch (a): bác sĩ tích tờ Phần 8 trong khi hồ sơ điện tử còn
        thiếu — G9-AUTO-08 phải REVIEW nói rõ 'tờ giấy không phải cổng', và
        trạng thái vẫn do các tiêu chí điện tử quyết (DRAFT), không phải do
        tờ giấy."""
        out_dir, _ = _evaluate_ready(tmp_path, monkeypatch)
        study = "PYTEST-G9Q"
        # Làm hồ sơ điện tử THIẾU thật: rút một xác nhận COI của tác giả 1.
        readiness_path = out_dir / G9Q.READINESS_JSON
        readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
        readiness["authors"][0]["coi_form_completed"] = False
        readiness_path.write_text(
            json.dumps(readiness, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        # Tích tờ Phần 8 trên A10 (thêm mục nếu fixture chưa có).
        a10 = out_dir / f"G9_A10_AUTHOR_INTEGRITY_{study}.md"
        text = a10.read_text(encoding="utf-8") if a10.exists() else "# A10\n"
        if not G9Q._PART8_HEADER_RE.search(text):
            text += "\n## Phần 8 — Tiêu chí Cổng G9 (Hard Gate)\n☐ Chưa ký\n"
        text += "\n☑ Đã ký đầy đủ\n☑ Đã kiểm chứng đầy đủ\n"
        a10.write_text(text, encoding="utf-8")

        report = G9Q.evaluate_study(study, out_dir, repo_root=tmp_path, write=True)
        row = _row(report, "G9-AUTO-08")
        assert row["status"] == "REVIEW", row
        assert "tờ giấy không phải cổng" in row["evidence"], row
        assert report["status"] == G9Q.STATUS_DRAFT
