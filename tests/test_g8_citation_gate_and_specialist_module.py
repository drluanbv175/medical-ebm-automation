# -*- coding: utf-8 -*-
"""Hồi quy vòng lặp kiểm tra-hoàn thiện vòng 12 (2026-07-23, dimension
g8_g9_remaining_depth, 2 phát hiện HIGH + 1 MEDIUM):

1. build_presubmission_checklist() trước đây dùng g0.get("_file_exists")
   (checkpoint TÌM KIẾM PUBMED — gần như luôn tồn tại rất sớm) làm proxy cho
   2 mục "Tất cả PMID/DOI đã xác minh" (LIÊM CHÍNH) và "Tài liệu tham khảo
   theo định dạng tạp chí đích" (TRÌNH BÀY) — hoàn toàn không phản ánh việc
   agent kiem-chung-trich-dan (cổng A12 thật) đã chạy/PASS hay chưa. Nay dùng
   run_g10_assemble.py::citation_verification_ok() — cùng cơ chế thật.

2. generate_a9_artifact()'s Phần 7 "TIÊU CHÍ QUA CỔNG G8" trước đây tự tính
   MỘT BẢN SAO RIÊNG irb_ok/sap_ok/g7_ok/score_ok chỉ để hiển thị, trôi dạt
   khỏi logic g8_status THẬT trong main() (vốn còn có results_final — điều
   kiện CHẶN thật). Nay nhận gate_criteria từ main() làm nguồn sự thật duy
   nhất, và results_final xuất hiện trong bảng BẮT BUỘC.

3. build_reporting_checklist() trước đây không đọc specialist_modules (vd
   'economic' — CHEERS 2022, đã nối ở G7 từ vòng 11) nên điểm % checklist
   không bao giờ phản ánh cấu phần cộng thêm.
"""
from __future__ import annotations

import os
import shutil
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import pytest  # noqa: E402
import run_g8_auto as G8  # noqa: E402

from tests.test_g10_submission_gate_required import (  # noqa: E402
    _configure_test_signing_key,
    _write_clean_citation_artifact,
)

# HERMETIC (16/08/2026): 2 điểm dưới đây gọi MẠNG THẬT (A12 xác minh trích dẫn
# sống); CI chặn outbound nên fail-closed ĐÚNG và test đỏ oan. Đánh dấu HẸP —
# phần còn lại của module vẫn chạy trong CI.
_CAN_MANG = pytest.mark.skipif(
    os.environ.get("MRAQ_OFFLINE_CI") == "1",
    reason="cần mạng outbound thật — hermetic CI chặn socket",
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


@_CAN_MANG
class TestCitationCheckUsesRealA12Gate:
    def test_no_a12_artifact_means_pmid_item_fails_despite_g0_existing(self):
        study = "PYTEST-G8-A12-T1"
        d = _study_dir(study)
        try:
            # G0 checkpoint TỒN TẠI (từng khiến item cũ luôn PASS) nhưng KHÔNG
            # có artifact A12 nào — item phải FALSE.
            result = G8.build_presubmission_checklist(
                _PIPELINE, _REPORTING, _STAT_CHECK, _BASE_GATES, [],
                study=study, out_dir=d,
            )
            pmid_item = next(i for i in result["items"] if "PMID/DOI" in i["description"])
            assert pmid_item["passed"] is False, (
                "Thiếu artifact A12 nhưng item vẫn PASS — hồi quy về proxy g0._file_exists cũ"
            )
        finally:
            _rmtree_retry(d)

    def test_clean_a12_artifact_makes_both_items_pass(self, tmp_path, monkeypatch):
        study = "PYTEST-G8-A12-T2"
        d = _study_dir(study)
        try:
            # Khóa ký TEST (vá 2026-08-17): receipt A12 phải mang chữ ký khớp khóa
            # đang cấu hình; dựa vào khóa THẬT của máy khiến test đỏ trên máy mới
            # chưa chạy setup_gate_approval_key.py (đo trên Windows) — cùng khuôn
            # với mọi test trong test_g10_submission_gate_required.py.
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_clean_citation_artifact(d, study)
            result = G8.build_presubmission_checklist(
                _PIPELINE, _REPORTING, _STAT_CHECK, _BASE_GATES, [],
                study=study, out_dir=d,
            )
            pmid_item = next(i for i in result["items"] if "PMID/DOI" in i["description"])
            ref_item = next(i for i in result["items"] if "dinh dang tap chi" in i["description"])
            assert pmid_item["passed"] is True
            assert ref_item["passed"] is True
        finally:
            _rmtree_retry(d)

    def test_missing_study_or_out_dir_defaults_to_false_no_crash(self):
        result = G8.build_presubmission_checklist(
            _PIPELINE, _REPORTING, _STAT_CHECK, _BASE_GATES, [],
        )
        pmid_item = next(i for i in result["items"] if "PMID/DOI" in i["description"])
        assert pmid_item["passed"] is False


def _real_presubmission(study: str, d: Path) -> dict:
    return G8.build_presubmission_checklist(
        _PIPELINE, _REPORTING, _STAT_CHECK, _BASE_GATES, [],
        study=study, out_dir=d,
    )


class TestGateCriteriaSingleSourceOfTruth:
    def test_gate_criteria_dict_drives_phan7_table_not_recomputed(self):
        """gate_criteria=None (mặc định) tính lại như cũ; gate_criteria truyền
        vào PHẢI được dùng nguyên trạng, kể cả khi mâu thuẫn với gates dict."""
        study = "PYTEST-G8-GC-T1"
        d = _study_dir(study)
        try:
            gate_criteria_all_false = {
                "irb_ok": False, "sap_ok": False, "g7_ok": False,
                "score_ok": False, "results_final": False,
            }
            md = G8.generate_a9_artifact(
                study, "2026-07-23", _BASE_GATES, _PIPELINE, _REPORTING,
                _STAT_CHECK, [], _real_presubmission(study, d),
                "", 0.0, "PENDING", gate_criteria=gate_criteria_all_false,
            )
            # Dù gates["G2"] có IRB thật (irb_ok lẽ ra True nếu tự tính lại),
            # phải dùng ĐÚNG gate_criteria truyền vào (False) — chứng minh
            # không tự tính lại một bản sao riêng.
            assert "ND 1. G2 LOCKED" in md
        finally:
            _rmtree_retry(d)

    def test_results_final_appears_in_mandatory_table(self):
        study = "PYTEST-G8-GC-T2"
        d = _study_dir(study)
        try:
            gate_criteria = {
                "irb_ok": True, "sap_ok": True, "g7_ok": True,
                "score_ok": True, "results_final": True,
            }
            md = G8.generate_a9_artifact(
                study, "2026-07-23", _BASE_GATES, _PIPELINE, _REPORTING,
                _STAT_CHECK, [], _real_presubmission(study, d),
                "", 0.0, "PASS", gate_criteria=gate_criteria,
            )
            assert "Ket qua phan tich THAT da xac nhan" in md
            assert "OK 4." in md  # results_final là mục 4 trong BAT BUOC
        finally:
            _rmtree_retry(d)

    def test_results_final_missing_shows_nd_and_blocks(self):
        study = "PYTEST-G8-GC-T3"
        d = _study_dir(study)
        try:
            gate_criteria = {
                "irb_ok": True, "sap_ok": True, "g7_ok": True,
                "score_ok": True, "results_final": False,
            }
            md = G8.generate_a9_artifact(
                study, "2026-07-23", _BASE_GATES, _PIPELINE, _REPORTING,
                _STAT_CHECK, [], _real_presubmission(study, d),
                "", 0.0, "PENDING", gate_criteria=gate_criteria,
            )
            assert "ND 4." in md
        finally:
            _rmtree_retry(d)


class TestSpecialistModuleChecklistWiring:
    def test_economic_specialist_module_attaches_cheers_checklist(self):
        result = G8.build_reporting_checklist("rct", _BASE_GATES, specialist_modules=["economic"])
        sm = result["specialist_module_checklist"]
        assert sm is not None
        assert sm["standard_name"] == "CHEERS 2022"
        assert sm["total"] == 28

    def test_no_specialist_module_means_none(self):
        result = G8.build_reporting_checklist("rct", _BASE_GATES, specialist_modules=[])
        assert result["specialist_module_checklist"] is None

    def test_economic_as_primary_design_not_duplicated(self):
        """Nếu design_code CHÍNH đã là 'economic' (bác sĩ PIN trực tiếp), không
        nối thêm checklist CHEERS thứ 2 dù specialist_modules cũng liệt kê nó."""
        result = G8.build_reporting_checklist("economic", _BASE_GATES, specialist_modules=["economic"])
        assert result["specialist_module_checklist"] is None
        assert result["standard_name"] == "CHEERS 2022"


class TestPresubmissionCoiCoverLetterUseRealGateParams:
    """Hồi quy audit tautology vòng 2 (2026-07-31, CRITICAL ceiling bug):
    trước bản vá, mục COI và Cover-letter trong build_presubmission_checklist()
    hardcode False vô điều kiện — không tham số nào của hàm (kể cả gates đầy
    đủ nhất) có thể khiến chúng True, khiến điểm tối đa đạt được đúng bằng
    ngưỡng 25/30 (0 dư), cùng lớp lỗi reverse-tautology đã gặp ở G2-AUTO-08/09.
    Nay dùng lại gate_params.G8.cover_letter_* — CHÍNH ground-truth mà
    g8_quality_gate.py::G8-AUTO-09 đã đọc cho cùng mục đích."""

    def _coi_item(self, result):
        return next(i for i in result["items"] if "Xung dot loi ich" in i["description"])

    def _cover_item(self, result):
        return next(i for i in result["items"] if "Cover letter" in i["description"])

    def test_no_gate_params_g8_means_coi_and_cover_letter_false(self):
        result = G8.build_presubmission_checklist(
            _PIPELINE, _REPORTING, _STAT_CHECK, _BASE_GATES, [],
        )
        assert self._coi_item(result)["passed"] is False
        assert self._cover_item(result)["passed"] is False

    def test_coi_declared_true_makes_coi_item_pass(self):
        result = G8.build_presubmission_checklist(
            _PIPELINE, _REPORTING, _STAT_CHECK, _BASE_GATES, [],
            gate_params_g8={"cover_letter_coi_declared": True},
        )
        assert self._coi_item(result)["passed"] is True

    def test_partial_cover_letter_fields_still_fails(self):
        """4/5 field — chưa đủ, vẫn False (không được PASS non oan)."""
        result = G8.build_presubmission_checklist(
            _PIPELINE, _REPORTING, _STAT_CHECK, _BASE_GATES, [],
            gate_params_g8={
                "cover_letter_no_duplicate_submission": True,
                "cover_letter_coi_declared": True,
                "cover_letter_all_authors_approved": True,
                "cover_letter_corresponding_contact": True,
                # thiếu cover_letter_preprint_status
            },
        )
        item = self._cover_item(result)
        assert item["passed"] is False
        assert "cover_letter_preprint_status" in item["note"]

    def test_all_5_cover_letter_fields_true_makes_item_pass(self):
        result = G8.build_presubmission_checklist(
            _PIPELINE, _REPORTING, _STAT_CHECK, _BASE_GATES, [],
            gate_params_g8={
                "cover_letter_no_duplicate_submission": True,
                "cover_letter_coi_declared": True,
                "cover_letter_all_authors_approved": True,
                "cover_letter_corresponding_contact": True,
                "cover_letter_preprint_status": True,
            },
        )
        assert self._cover_item(result)["passed"] is True

    @_CAN_MANG
    def test_ceiling_now_above_threshold_with_realistic_complete_study(self, tmp_path, monkeypatch):
        """Đóng CHẶT bug ceiling=threshold: với mọi mục THẬT SỰ khả thi đạt
        True (bao gồm COI/Cover-letter qua gate_params.G8 mới), tổng điểm
        phải VƯỢT ngưỡng 25, không chỉ chạm đúng ngưỡng — xác nhận còn dư ít
        nhất 1 điểm biên (trước bản vá: ceiling tuyệt đối = 25, dư = 0)."""
        full_gates = {
            "G0": {"_file_exists": True, "pubmed_results": {"n_sr": 2, "n_rct": 3}},
            "G1": {"_file_exists": True},
            "G2": {"_file_exists": True, "g2_irb_number": "IRB-2026-001",
                   "g2_registration": "NCT00000001"},
            "G3": {"_file_exists": True},
            "G4": {"_file_exists": True, "sap_signed_date": "2026-07-01"},
            "G5": {"_file_exists": True, "db_lock_date": "2026-07-10"},
            "G6": {"_file_exists": True},
            "G7": {"_file_exists": True},
        }
        full_pipeline = {"n_pass": 8, "n_total": 8, "completeness_pct": 100, "rows": []}
        full_reporting = {"standard_name": "STROBE 2007", "score_pct": 90,
                           "checked": 5, "total": 5, "items": [],
                           "specialist_module_checklist": None}
        full_stat_check = {"passed_count": 5, "total_checks": 5, "overall": "OK", "warnings": []}
        study = "PYTEST-G8-CEILING-T1"
        d = _study_dir(study)
        try:
            # Khóa ký TEST (vá 2026-08-17) — cùng lý do với TestCitationCheckUsesRealA12Gate.
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_clean_citation_artifact(d, study)  # A12 sạch -> 2 mục PMID/DOI+định dạng PASS
            result = G8.build_presubmission_checklist(
                full_pipeline, full_reporting, full_stat_check, full_gates, [],
                study=study, out_dir=d,
                gate_params_g8={
                    "cover_letter_no_duplicate_submission": True,
                    "cover_letter_coi_declared": True,
                    "cover_letter_all_authors_approved": True,
                    "cover_letter_corresponding_contact": True,
                    "cover_letter_preprint_status": True,
                },
            )
        finally:
            _rmtree_retry(d)
        # Author list/ORCID, Tiêu đề, Tóm tắt vẫn CỐ Ý [CẦN] (infeasible bằng
        # máy) — nên trần thật KHÔNG PHẢI 30, nhưng phải > 25 (ngưỡng nộp).
        assert result["passed"] > 25, (
            f"Ceiling vẫn chạm đúng ngưỡng (passed={result['passed']}) — bug reverse-tautology "
            "chưa thực sự đóng"
        )
