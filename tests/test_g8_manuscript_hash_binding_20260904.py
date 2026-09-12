# -*- coding: utf-8 -*-
"""Hồi quy phát hiện HIGH (audit đa-agent 2026-09-04): chữ ký G8 chỉ băm
G8_A9_PRESUBMISSION_<study>.md (bản TỰ KIỂM do máy sinh) — KHÔNG BAO GIỜ băm
G7_A8_MANUSCRIPT_<study>.md (bản thảo thật). Người phản biện ký G8 trên A9,
sau đó bản thảo có thể bị sửa (đổi hiệu số, thêm trích dẫn đã rút, xóa cảnh
báo an toàn) mà chữ ký vẫn báo "hợp lệ" — không có kiểm tra nào, kể cả
run_g10_assemble.py, từng phát hiện việc này.

Vá ba lớp:
  (A) run_g8_auto.py::generate_a9_artifact() nhúng SHA-256 bản thảo vào A9
      NGAY LÚC sinh -- chữ ký đã có transitively ràng buộc luôn bản thảo.
  (B) g8_quality_gate.py: G8-AUTO-12 đối chiếu hash nhúng với hash SỐNG của
      bản thảo hiện tại (dùng khi bác sĩ chạy lại g8_quality_gate.py sau
      khi đã ký).
  (C) run_g10_assemble.py: chốt CHẶN THẬT -- đây là điểm duy nhất thực sự
      "khóa" gói trước khi xuất cho hội đồng/tạp chí, nên đối chiếu lại
      TẠI ĐÂY (không chỉ ở lúc ký) mới đóng được lỗ hổng cho kịch bản
      "sửa bản thảo SAU KHI G8 đã ký rồi vẫn lắp gói bình thường".

File này test cả ba lớp bằng dữ liệu THẬT (không mock hashlib/regex):
  1. generate_a9_artifact() nhúng đúng định dạng mà _trich_hash_ban_thao_
     da_ky() trích lại được nguyên vẹn (round-trip qua chính hai hàm thật).
  2. evaluate_g8_quality() (G8-AUTO-12) phân loại đúng PASS/REVIEW/BLOCK
     theo đúng ma trận (khớp/lệch × đã ký/chưa ký × có/không nhúng hash).
  3. run_g10_assemble.main() -- ★★ ca chính đúng kịch bản của phát hiện:
     ký G8 xong, sửa bản thảo, gọi lại G10 -> phải CHẶN với lý do mới
     REASON_MANUSCRIPT_CHANGED_AFTER_PEER_REVIEW; cờ --i-know-g8-manuscript
     -changed cho xem trước; bản thảo khớp hash (không đổi) hoặc A9 định
     dạng cũ (không có hash nhúng) đều KHÔNG được chặn oan.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import g8_quality_gate as G8Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_g8_auto as G8  # noqa: E402

from tests.test_g10_assemble import _write_cross_sectional_fixture  # noqa: E402
from tests.test_g10_submission_gate_required import (  # noqa: E402
    _configure_test_signing_key,
    _run_main,
    _write_clean_citation_artifact,
    _write_ledger_approval,
)


def _rmtree_retry(d: Path, attempts: int = 5, delay_s: float = 0.2) -> None:
    for _ in range(attempts):
        if not d.exists():
            return
        shutil.rmtree(d, ignore_errors=True)
        if not d.exists():
            return
        time.sleep(delay_s)


def _study_dir(name: str) -> Path:
    d = REPO_ROOT / "exports" / name
    _rmtree_retry(d)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _read_g10_needs_input(d: Path) -> dict:
    cp = json.loads((d / "G10_checkpoint.json").read_text(encoding="utf-8"))
    assert GC.is_blocked(cp)
    return cp["needs_input"]


# ── Bộ đối số tối giản cho generate_a9_artifact(), khuôn theo
# tests/test_g8_citation_gate_and_specialist_module.py — CHỈ dùng để dựng A9,
# không phụ thuộc mạng/ledger.
_BASE_GATES = {
    "G0": {"_file_exists": True, "pubmed_results": {"n_sr": 1, "n_rct": 2}},
    "G1": {"_file_exists": True},
    "G2": {"_file_exists": True, "g2_irb_number": "IRB-2026-001"},
    "G3": {"_file_exists": True},
    "G4": {"_file_exists": True, "sap_signed_date": "2026-07-01"},
    "G5": {"_file_exists": True, "db_lock_date": "2026-07-10"},
    "G6": {"_file_exists": True},
    "G7": {"_file_exists": True},
}
_PIPELINE = {"n_pass": 8, "n_total": 8, "completeness_pct": 100, "rows": []}
_REPORTING = {"standard_name": "STROBE 2007", "score_pct": 80, "checked": 4, "total": 5, "items": []}
_STAT_CHECK = G8.check_statistical_integrity(_BASE_GATES)


def _build_a9(study: str, d: Path, manuscript_sha256, manuscript_filename) -> str:
    presubmission = G8.build_presubmission_checklist(
        _PIPELINE, _REPORTING, _STAT_CHECK, _BASE_GATES, [], study=study, out_dir=d,
    )
    return G8.generate_a9_artifact(
        study, "2026-09-04", _BASE_GATES, _PIPELINE, _REPORTING, _STAT_CHECK, [],
        presubmission, "", 0.0, "PENDING",
        manuscript_sha256=manuscript_sha256, manuscript_filename=manuscript_filename,
    )


class TestGenerateA9EmbedsExtractableHash:
    """Lớp (A) — round-trip THẬT qua generate_a9_artifact() và
    g8_quality_gate._trich_hash_ban_thao_da_ky(), không mock chuỗi/regex."""

    def test_hash_nhung_dung_va_trich_lai_khop(self):
        study = "PYTEST-G8HASH-A1"
        d = _study_dir(study)
        try:
            manuscript_text = "Nội dung bản thảo thật — hiệu số HR=0.72 (95% CI 0.61-0.85)."
            expected = hashlib.sha256(manuscript_text.encode("utf-8")).hexdigest()
            md = _build_a9(study, d, expected, f"G7_A8_MANUSCRIPT_{study}.md")
            assert f"`{expected}`" in md, "A9 phải in NGUYÊN VĂN hash SHA-256 (64 hex, giữa dấu backtick)"
            trich = G8Q._trich_hash_ban_thao_da_ky(md)
            assert trich == expected, "Trích lại từ A9 phải khớp BYTE-EXACT hash đã nhúng"
        finally:
            _rmtree_retry(d)

    def test_khong_co_ban_thao_thi_khong_nhung_hash_gia(self):
        """manuscript_sha256=None (bản thảo chưa tồn tại lúc sinh A9) -- A9
        phải nói rõ CHƯA CÓ, không được bịa/để trống mà vẫn trông như đã ràng
        buộc (fail-closed: _trich_hash_ban_thao_da_ky() phải trả None)."""
        study = "PYTEST-G8HASH-A2"
        d = _study_dir(study)
        try:
            md = _build_a9(study, d, None, f"G7_A8_MANUSCRIPT_{study}.md")
            assert "CHƯA CÓ BẢN THẢO" in md
            assert G8Q._trich_hash_ban_thao_da_ky(md) is None
        finally:
            _rmtree_retry(d)

    def test_hai_ban_thao_khac_nhau_ra_hash_khac_nhau(self):
        """Đối chứng cơ bản: hash không phải hằng số/luôn cùng một giá trị."""
        study = "PYTEST-G8HASH-A3"
        d = _study_dir(study)
        try:
            h1 = hashlib.sha256("bản thảo v1".encode("utf-8")).hexdigest()
            h2 = hashlib.sha256("bản thảo v2 — đã sửa hiệu số".encode("utf-8")).hexdigest()
            assert h1 != h2
            md1 = _build_a9(study, d, h1, "X.md")
            assert G8Q._trich_hash_ban_thao_da_ky(md1) == h1
            assert G8Q._trich_hash_ban_thao_da_ky(md1) != h2
        finally:
            _rmtree_retry(d)


class TestTrichHashRegexEdgeCases:
    """Lớp (B) — helper trích xuất phải KHÔNG dương tính giả trên định dạng
    cũ/hỏng, và không nhạy với hoa/thường của tiêu đề nhãn."""

    def test_van_ban_khong_co_nhan_tra_none(self):
        assert G8Q._trich_hash_ban_thao_da_ky("A9 định dạng cũ, không có nhãn hash nào.") is None

    def test_van_ban_rong_tra_none(self):
        assert G8Q._trich_hash_ban_thao_da_ky("") is None
        assert G8Q._trich_hash_ban_thao_da_ky(None) is None

    def test_hash_qua_ngan_khong_khop(self):
        """63 hex char (thiếu 1) không phải SHA-256 hợp lệ -- không được trích."""
        text = "**Hash SHA-256 bản thảo đã ràng buộc (`x.md`):** `" + "a" * 63 + "`"
        assert G8Q._trich_hash_ban_thao_da_ky(text) is None

    def test_hash_ky_tu_khong_phai_hex_khong_khop(self):
        text = "**Hash SHA-256 bản thảo đã ràng buộc (`x.md`):** `" + "g" * 64 + "`"
        assert G8Q._trich_hash_ban_thao_da_ky(text) is None


class TestEvaluateG8QualityAuto12Matrix:
    """Lớp (B) — G8-AUTO-12 trong evaluate_g8_quality(): ma trận đầy đủ
    khớp/lệch × đã ký/chưa ký × có/không nhúng hash. Dùng A9 THẬT do
    generate_a9_artifact() sinh (không tự viết chuỗi giả lập định dạng)."""

    def _find(self, report: dict, cid: str) -> dict:
        for row in report["automatic_criteria"]:
            if row["id"] == cid:
                return row
        raise AssertionError(f"Không thấy {cid} trong automatic_criteria")

    def _evaluate(self, study, d, presubmission_text, manuscript_text, ledger_signed):
        return G8Q.evaluate_g8_quality(
            study=study, checkpoint={}, presubmission_text=presubmission_text,
            manuscript_text=manuscript_text, sap_text="", review_report_text="",
            g2_checkpoint={}, meta={}, citation_ok=True, citation_detail="",
            ledger_signed=ledger_signed, ledger_reason="", signature_scope=None,
            role_key_available=False, cross_gate_refs={}, design_drift_warning=None,
        )

    def test_hash_khop_thi_pass(self):
        study = "PYTEST-G8HASH-B1"
        d = _study_dir(study)
        try:
            manuscript_text = "bản thảo chưa đổi"
            h = hashlib.sha256(manuscript_text.encode("utf-8")).hexdigest()
            a9 = _build_a9(study, d, h, "X.md")
            report = self._evaluate(study, d, a9, manuscript_text, ledger_signed=True)
            row = self._find(report, "G8-AUTO-12")
            assert row["status"] == "PASS", row
        finally:
            _rmtree_retry(d)

    def test_hash_lech_va_da_ky_thi_block(self):
        """★★ Ca chính: bản thảo bị sửa SAU KHI A9 được sinh/ký -- lỗ hổng
        gốc của phát hiện. ledger_signed=True mô phỏng "đã ký thật"."""
        study = "PYTEST-G8HASH-B2"
        d = _study_dir(study)
        try:
            manuscript_luc_ky = "hiệu số HR=0.72 (95% CI 0.61-0.85)"
            h_luc_ky = hashlib.sha256(manuscript_luc_ky.encode("utf-8")).hexdigest()
            a9 = _build_a9(study, d, h_luc_ky, "X.md")
            manuscript_sau_khi_sua = "hiệu số HR=0.40 (95% CI 0.10-0.99) — ĐÃ BỊ SỬA"
            report = self._evaluate(study, d, a9, manuscript_sau_khi_sua, ledger_signed=True)
            row = self._find(report, "G8-AUTO-12")
            assert row["status"] == "BLOCK", row
            assert "ĐÃ ĐƯỢC KÝ" in row["evidence"]
        finally:
            _rmtree_retry(d)

    def test_hash_lech_nhung_chua_ky_thi_chi_review(self):
        """Sửa bản thảo TRƯỚC KHI ký là soạn thảo bình thường -- không chặn."""
        study = "PYTEST-G8HASH-B3"
        d = _study_dir(study)
        try:
            h_cu = hashlib.sha256("bản nháp đầu".encode("utf-8")).hexdigest()
            a9 = _build_a9(study, d, h_cu, "X.md")
            report = self._evaluate(study, d, a9, "bản nháp đã sửa tiếp — chưa ký gì cả",
                                     ledger_signed=False)
            row = self._find(report, "G8-AUTO-12")
            assert row["status"] == "REVIEW", row
        finally:
            _rmtree_retry(d)

    def test_khong_co_hash_nhung_a9_dinh_dang_cu_thi_pass_khong_block(self):
        """A9 sinh TRƯỚC bản vá này (không có nhãn hash) -- không được suy
        diễn thành "đã bị sửa" (BH08: biến chưa biết thành có vấn đề).

        SỬA: bản đầu của check này trả REVIEW cho trường hợp này, nhưng
        auto_review = any(status=="REVIEW") kéo report["status"] TOÀN BỘ về
        STATUS_DRAFT vô điều kiện -- nghĩa là MỌI đề tài đã ký G8 THẬT trước
        khi bản vá này tồn tại (100% số đề tài hiện có) sẽ đồng loạt "tụt
        hạng" từ PASS_G8_REVIEW_RECORDED xuống DRAFT_NEEDS_HUMAN_COMPLETION
        dù không có gì thay đổi -- đúng lớp lỗi BH08 mà chính comment ở đó
        định tránh, chỉ là áp SAI hướng. Bắt bằng cách chạy bộ test hồi quy
        đầy đủ tests/test_g8_quality_gate.py (6 test đỏ trước khi sửa lại
        thành PASS). Test này khoá lại: PASS, không REVIEW."""
        study = "PYTEST-G8HASH-B4"
        report = self._evaluate(
            study, REPO_ROOT / "exports" / study,
            "# A9 định dạng CŨ\nKhông có nhãn hash bản thảo nào ở đây.\n",
            "bản thảo bất kỳ", ledger_signed=True,
        )
        row = self._find(report, "G8-AUTO-12")
        assert row["status"] == "PASS", row
        assert "định dạng cũ" in row["evidence"]

    def test_khong_co_hash_khong_keo_status_tong_ve_draft(self):
        """★★ Đối chứng trực tiếp cho regression vừa vá, dùng CHÍNH fixture
        "mọi tiêu chí khác đều PASS" của tests/test_g8_quality_gate.py (nơi
        đã đo được: bản đầu của G8-AUTO-12 làm 6 test ở đó đỏ vì report["status"]
        tụt từ STATUS_REVIEWED xuống STATUS_DRAFT). presubmission_text của
        fixture đó là chuỗi viết tay, KHÔNG có nhãn hash nhúng — đúng kịch bản
        "đề tài đã ký G8 THẬT trước khi bản vá 2026-09-04 tồn tại"."""
        from tests.test_g8_quality_gate import _evaluate as _evaluate_fully_green

        report = _evaluate_fully_green()
        row = self._find(report, "G8-AUTO-12")
        assert row["status"] == "PASS", row
        assert report["status"] == G8Q.STATUS_REVIEWED, (
            f"Thiếu hash nhúng (đề tài ký TRƯỚC bản vá này) không được tự nó "
            f"kéo trạng thái tổng thể của G8 xuống DRAFT — xem CLAUDE.md BH08. "
            f"status thật: {report['status']}")

    def test_khong_co_ban_thao_song_thi_review(self):
        study = "PYTEST-G8HASH-B5"
        d = _study_dir(study)
        try:
            h = hashlib.sha256("x".encode("utf-8")).hexdigest()
            a9 = _build_a9(study, d, h, "X.md")
            report = self._evaluate(study, d, a9, "", ledger_signed=True)
            row = self._find(report, "G8-AUTO-12")
            assert row["status"] == "REVIEW", row
        finally:
            _rmtree_retry(d)


class TestG10BlocksManuscriptTamperedAfterSigning:
    """Lớp (C) — ★★ ca chính đúng nguyên văn kịch bản của phát hiện, chạy
    qua CLI THẬT run_g10_assemble.main() (không mock): ký G8 xong, sửa bản
    thảo, gọi G10 lại -- phải bị CHẶN, không được lắp gói "sẵn sàng nộp"."""

    def _seed_and_sign_g8(self, d: Path, study: str, manuscript_text: str) -> None:
        _write_cross_sectional_fixture(d)
        _write_clean_citation_artifact(d, study)
        (d / f"G9_A10_AUTHOR_INTEGRITY_{study}.md").write_text(
            "AUTHOR INTEGRITY — nội dung giả lập test", encoding="utf-8", newline="\n")
        _write_ledger_approval(
            d, "G9", "AUTHOR INTEGRITY — nội dung giả lập test", "PI_PROJECT_OWNER")
        (d / f"G7_A8_MANUSCRIPT_{study}.md").write_text(
            manuscript_text, encoding="utf-8", newline="\n")
        manuscript_hash = hashlib.sha256(manuscript_text.encode("utf-8")).hexdigest()
        a9 = _build_a9(study, d, manuscript_hash, f"G7_A8_MANUSCRIPT_{study}.md")
        (d / f"G8_A9_PRESUBMISSION_{study}.md").write_text(a9, encoding="utf-8", newline="\n")
        _write_ledger_approval(d, "G8", a9, "PHAN_BIEN_DOC_LAP")

    def test_ban_thao_doi_sau_khi_ky_thi_bi_chan(self, tmp_path, monkeypatch):
        study = "PYTEST-G10HASH-C1"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            self._seed_and_sign_g8(d, study, "hiệu số HR=0.72 -- bản người phản biện đã đọc")
            # Sửa bản thảo SAU KHI G8 đã ký -- đúng kịch bản của phát hiện.
            (d / f"G7_A8_MANUSCRIPT_{study}.md").write_text(
                "hiệu số HR=0.40 -- ĐÃ SỬA SAU KHI KÝ, người phản biện chưa từng thấy",
                encoding="utf-8", newline="\n")
            rc = _run_main(study)
            assert rc == GC.EXIT_BLOCKED, "Bản thảo đổi sau khi ký PHẢI chặn G10, không được lắp gói 'sẵn sàng nộp'"
            assert (_read_g10_needs_input(d)["reason_code"]
                    == GC.REASON_MANUSCRIPT_CHANGED_AFTER_PEER_REVIEW)
        finally:
            _rmtree_retry(d)

    def test_co_bypass_flag_thi_van_lap_gio_ban_nhap_nhung_khong_pass(self, tmp_path, monkeypatch):
        study = "PYTEST-G10HASH-C2"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            self._seed_and_sign_g8(d, study, "bản gốc")
            (d / f"G7_A8_MANUSCRIPT_{study}.md").write_text(
                "bản đã sửa sau ký", encoding="utf-8", newline="\n")
            rc = _run_main(study, ["--i-know-g8-manuscript-changed"])
            assert rc == GC.EXIT_GUARDRAIL_FAIL, (
                "Cờ xem-trước không được trả 0 (thành công) -- vẫn phải nói rõ chưa đủ điều kiện nộp")
            md_text = (d / f"DE_CUONG_THONG_NHAT_{study}.md").read_text(encoding="utf-8")
            assert "--i-know-g8-manuscript-changed" in md_text, (
                "Banner cảnh báo phải xuất hiện TRONG chính tài liệu, không chỉ ở stdout")
        finally:
            _rmtree_retry(d)

    def test_ban_thao_khong_doi_thi_khong_bi_chan_boi_check_moi(self, tmp_path, monkeypatch):
        """Đối chứng BẮT BUỘC: bản thảo giữ nguyên sau khi ký -- G10 phải qua
        được tới cuối (rc == 0), bản vá không được biến mọi lượt ký G8 thành
        chặn oan."""
        study = "PYTEST-G10HASH-C3"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            self._seed_and_sign_g8(d, study, "bản thảo không hề đổi sau khi ký")
            rc = _run_main(study)
            assert rc == 0, "Bản thảo không đổi -- không được chặn bởi G8-manuscript-hash check"
        finally:
            _rmtree_retry(d)

    def test_a9_dinh_dang_cu_khong_co_hash_khong_bi_chan_oan(self, tmp_path, monkeypatch):
        """Tương thích ngược: đề tài đã ký G8 TRƯỚC bản vá này (A9 không có
        nhãn hash nhúng) -- không được diễn giải thành "đã bị sửa" và chặn
        một đề tài hợp lệ đã ký từ trước (BH08)."""
        study = "PYTEST-G10HASH-C4"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            _write_clean_citation_artifact(d, study)
            (d / f"G9_A10_AUTHOR_INTEGRITY_{study}.md").write_text(
                "AUTHOR INTEGRITY — nội dung giả lập test", encoding="utf-8", newline="\n")
            _write_ledger_approval(
                d, "G9", "AUTHOR INTEGRITY — nội dung giả lập test", "PI_PROJECT_OWNER")
            (d / f"G7_A8_MANUSCRIPT_{study}.md").write_text(
                "bản thảo bất kỳ, không liên quan", encoding="utf-8", newline="\n")
            g8_content_dinh_dang_cu = "PRESUBMISSION REVIEW — nội dung giả lập test (KHÔNG có hash nhúng)"
            (d / f"G8_A9_PRESUBMISSION_{study}.md").write_text(
                g8_content_dinh_dang_cu, encoding="utf-8", newline="\n")
            _write_ledger_approval(d, "G8", g8_content_dinh_dang_cu, "PHAN_BIEN_DOC_LAP")
            rc = _run_main(study)
            assert rc == 0, "A9 định dạng cũ (chưa có hash nhúng) không được chặn oan"
        finally:
            _rmtree_retry(d)


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
