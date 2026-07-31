"""Hồi quy G10-03 (audit toàn diện G0-G10, 2026-07-30, HIGH):

Trước vá này, KHÔNG test nào chạy `run_g10_assemble.assemble()` THẬT rồi đưa
CHÍNH output đó vào `g10_quality_gate.evaluate_study()` THẬT:
- tests/test_g10_assemble.py chỉ gọi assemble(), không bao giờ chấm bằng
  g10_quality_gate.
- tests/test_g10_quality_gate.py::_write_ready_fixture tự viết tay nội dung
  markdown thay vì gọi assemble() thật.
- tests/test_g10_submission_gate_required.py::TestModernG10ReleaseContract
  monkeypatch hẳn G10Q.evaluate_study() bằng lambda trả cứng STATUS_READY/
  STATUS_LOCKED — không bao giờ chạy hàm THẬT.

Kết hợp với G10-01 (g4_ok vĩnh viễn False) và G10-02 (placeholder-legend tự
fail vĩnh viễn), đây chính là lý do bộ ~40 test trước đó không bắt được rằng
tính năng khóa gói phát hành G10 không thể hoàn tất trên dữ liệu thật — cả
2 lỗi đó chỉ lộ ra khi chạy assemble() thật rồi chấm bằng g10_quality_gate
thật trên CÙNG một output, việc mà không test nào từng làm.

File này nối trọn 2 hàm thật trên CÙNG một checkpoint fixture (tái dùng
_write_cross_sectional_fixture của test_g10_assemble.py — fixture xây tay
checkpoint G0-G9 nhưng KHÔNG viết tay nội dung markdown/không mock
evaluate_study())."""

from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import g10_quality_gate as G10Q  # noqa: E402
import run_g10_assemble as G10  # noqa: E402
from tests.test_g10_assemble import _write_cross_sectional_fixture  # noqa: E402


def _row(report, criterion_id):
    for row in report["automatic_criteria"]:
        if row["id"] == criterion_id:
            return row
    raise AssertionError(f"Không tìm thấy tiêu chí {criterion_id}")


class TestRealAssembleFeedsRealEvaluateStudy:
    def test_incomplete_package_reaches_draft_not_ready_or_locked(self, tmp_path):
        """Fixture cố ý CHƯA ký G2/G4/G5/G8/G9 — kết quả THẬT phải là DRAFT,
        không phải READY/LOCKED giả do mock/fixture tay che giấu."""
        _write_cross_sectional_fixture(tmp_path, specialty="cardiology")
        G10.assemble("FIXT", tmp_path)

        report = G10Q.evaluate_study("FIXT", tmp_path, repo_root=tmp_path.parent, write=False)

        assert report["status"] == G10Q.STATUS_DRAFT
        assert report["status"] not in (G10Q.STATUS_READY, G10Q.STATUS_LOCKED)

    def test_no_criterion_crashes_or_returns_unknown_status(self, tmp_path):
        _write_cross_sectional_fixture(tmp_path, specialty="cardiology")
        G10.assemble("FIXT", tmp_path)
        report = G10Q.evaluate_study("FIXT", tmp_path, repo_root=tmp_path.parent, write=False)
        for row in report["automatic_criteria"]:
            assert row["status"] in ("PASS", "REVIEW", "BLOCK"), row

    def test_g4_ok_reflects_real_g4_contract_not_permanently_false(self, tmp_path):
        """Hồi quy G10-01: g4_ok trước đây vĩnh viễn False vì đọc g4_status
        text không bao giờ được ghi "LOCKED". Ở fixture CHƯA ký (g4_status=
        PENDING thật), G10-AUTO-04 phải REVIEW vì g4 THẬT SỰ chưa khóa — không
        phải vì cơ chế đọc sai field."""
        _write_cross_sectional_fixture(tmp_path, specialty="cardiology")
        G10.assemble("FIXT", tmp_path)
        report = G10Q.evaluate_study("FIXT", tmp_path, repo_root=tmp_path.parent, write=False)
        row = _row(report, "G10-AUTO-04")
        assert row["status"] == "REVIEW"
        assert "G4=False" in row["evidence"]

    def test_g4_ok_flips_true_when_real_contract_function_says_so(self, tmp_path, monkeypatch):
        """Đóng vòng G10-01 chặt hơn: nếu chỉ hardcode g4_ok=False (bất kể
        hàm hợp đồng thật trả gì) thì test này sẽ bắt được — mock
        g4_quality_contract_satisfied() trả True và xác nhận G10-AUTO-04 đọc
        ĐÚNG giá trị đó qua CHÍNH pipeline assemble()+evaluate_study() thật,
        không phải qua field text đã lỗi thời."""
        _write_cross_sectional_fixture(tmp_path, specialty="cardiology")
        G10.assemble("FIXT", tmp_path)
        monkeypatch.setattr(
            G10Q.GC, "g4_quality_contract_satisfied", lambda *_a, **_k: True
        )
        report = G10Q.evaluate_study("FIXT", tmp_path, repo_root=tmp_path.parent, write=False)
        row = _row(report, "G10-AUTO-04")
        assert "G4=True" in row["evidence"]

    def test_placeholder_legend_does_not_false_positive_block_g10_auto_09(self, tmp_path):
        """Hồi quy G10-02: build_front_note()/build_document_control() từng
        nhúng cứng cụm placeholder hợp lệ vào câu giải thích, khiến G10-AUTO-09
        (không placeholder) không bao giờ có thể PASS/REVIEW — luôn BLOCK giả.
        Ở đây thiếu file phụ trợ (A12/G8 peer review/G9 readiness) nên REVIEW
        là đúng — nhưng KHÔNG được là BLOCK do placeholder-legend tự nhúng."""
        _write_cross_sectional_fixture(tmp_path, specialty="cardiology")
        G10.assemble("FIXT", tmp_path)
        report = G10Q.evaluate_study("FIXT", tmp_path, repo_root=tmp_path.parent, write=False)
        row = _row(report, "G10-AUTO-09")
        assert row["status"] != "BLOCK", row
        assert "missing_or_unreadable" in row["evidence"]

    def test_rerunning_assemble_on_same_unlocked_study_is_idempotent(self, tmp_path):
        """assemble() gọi lại trên đề tài CHƯA khóa phải không lỗi (khác hẳn
        nhánh already_locked dành cho đề tài đã có chữ ký PI thật)."""
        _write_cross_sectional_fixture(tmp_path, specialty="cardiology")
        first = G10.assemble("FIXT", tmp_path)
        second = G10.assemble("FIXT", tmp_path)
        assert first["md"] == second["md"]
        assert not first.get("already_locked")
        assert not second.get("already_locked")


class TestFinalTechnicalCompletionAndStructuralSectionsNeverPermanentlyBlock:
    """Hồi quy audit tautology vòng 2 (2026-07-31, CRITICAL G10-AUTO-09):
    trước bản vá, 6 hàm sinh nội dung (build_phuluc, build_legal_refs,
    build_traceability_matrix, build_display_items,
    build_international_compliance, build_final_technical_completion) nhúng
    "[CẦN...]"/"[CẦN XÁC NHẬN TẠI ĐƠN VỊ]"/"[CẦN KIỂM CHỨNG NGUỒN CHÍNH THỨC]"
    VÔ ĐIỀU KIỆN vào final_protocol_md — g10_quality_gate._documents_clean()
    quét đúng các mẫu này (_PLACEHOLDER_RE) nên G10-AUTO-09 KHÔNG BAO GIỜ có
    thể PASS/không-BLOCK-vì-placeholder cho BẤT KỲ đề tài thật nào, dù mọi
    trường dữ liệu khác đã điền đầy đủ nhất có thể. Test này gọi assemble()
    THẬT (không viết tay markdown), điền study_meta.json gần như tối đa những
    gì các hàm trên có thể đọc, rồi xác nhận CHÍNH VĂN BẢN đã ghi ra đĩa
    không còn khớp _PLACEHOLDER_RE trong 6 mục đó — độc lập với các file phụ
    trợ khác (A12/G8/G9 readiness) mà _documents_clean() còn cần để tới được
    nhánh quét placeholder."""

    _SECTION_HEADERS = (
        "# Phụ lục",
        "# Khung pháp lý",
        "# Ma trận truy xuất",
        "# Danh mục bảng và hình",
        "# Ma trận tuân thủ tiêu chuẩn quốc tế",
        "# Bảng kiểm hoàn thành kỹ thuật",
    )

    def _assemble_with_rich_meta(self, tmp_path):
        _write_cross_sectional_fixture(tmp_path, specialty="cardiology")
        import json as _json
        meta_path = tmp_path / "study_meta.json"
        meta = _json.loads(meta_path.read_text(encoding="utf-8"))
        meta.update({
            "title": "Tỷ lệ tăng huyết áp chưa kiểm soát ở bệnh nhân đái tháo đường type 2",
            "aim": "Xác định tỷ lệ THA chưa kiểm soát và yếu tố liên quan",
            "research_question": "Tỷ lệ THA chưa kiểm soát ở BN ĐTĐ type 2 là bao nhiêu?",
            "objectives": ["Mô tả tỷ lệ THA chưa kiểm soát", "Xác định yếu tố liên quan"],
            "primary_outcome": "THA chưa kiểm soát (HA >=140/90 mmHg)",
            "exposure": "Thời gian mắc đái tháo đường",
            "prepared_by": "BS. Nguyễn Văn A",
            "org_lines": ["Khoa Nội tiết, Bệnh viện XYZ"],
            "place_year": "TP.HCM - 2026",
        })
        meta_path.write_text(_json.dumps(meta, ensure_ascii=False), encoding="utf-8")
        result = G10.assemble("FIXT", tmp_path)
        return Path(result["md"]).read_text(encoding="utf-8")

    def test_six_structural_sections_have_no_placeholder_regex_hits(self, tmp_path):
        import re as _re
        text = self._assemble_with_rich_meta(tmp_path)
        placeholder_re = _re.compile(
            r"\[(?:CẦN|CAN|TBD|TODO|PENDING)[^\]]*\]", _re.IGNORECASE
        )
        for header in self._SECTION_HEADERS:
            start = text.find(header)
            assert start >= 0, f"Không tìm thấy mục {header!r} trong final_protocol_md"
            end = text.find("\n# ", start + 1)
            if end < 0:
                end = len(text)
            chunk = text[start:end]
            hits = placeholder_re.findall(chunk)
            assert not hits, (
                f"Mục {header!r} vẫn còn placeholder vô điều kiện: {hits} — "
                "G10-AUTO-09 sẽ không bao giờ PASS được cho đề tài thật"
            )

    def test_new_manual_tag_still_visible_to_doctor_not_silently_dropped(self, tmp_path):
        """Đóng vòng an toàn: nhãn mới KHÔNG được biến mất khỏi tài liệu —
        chỉ đổi để không khớp _PLACEHOLDER_RE, bác sĩ vẫn phải thấy rõ đây là
        bước cần xác nhận thủ công."""
        text = self._assemble_with_rich_meta(tmp_path)
        assert text.count("[XÁC NHẬN THỦ CÔNG NGOÀI HỆ THỐNG]") >= 10, (
            "Nhãn thủ công mới phải xuất hiện đủ nhiều lần (Phụ lục, Khung "
            "pháp lý, 2 bảng Bảng kiểm hoàn thành kỹ thuật...) — không được "
            "biến mất khỏi tài liệu"
        )
