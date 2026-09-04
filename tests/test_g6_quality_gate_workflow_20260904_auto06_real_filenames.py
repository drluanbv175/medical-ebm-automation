# -*- coding: utf-8 -*-
"""Hồi quy phát hiện HIGH của Workflow đối kháng đa-agent vòng 3 (2026-09-04) trong
tools/g6_quality_gate.py::evaluate_study() — G6-AUTO-06.

Mẫu tên file GIẢ ĐỊNH của G6-AUTO-06 (*KET_QUA*/*RESULTS*/stats_output*) KHÔNG khớp
BẤT KỲ file thật nào mà tools/run_stats_analysis.py — cỗ máy phân tích DUY NHẤT của
repo — thực sự ghi ra (`{gate}_table1_descriptive.txt`, `{gate}_table2_main_outcome.txt`,
`{gate}_analysis_summary.json`, `{gate}_analysis_syntax.R`…). Luật sinh ra để bắt "đã
chạy phân tích TRƯỚC khi khoá dữ liệu" (đúng kịch bản HARKing/p-hacking mà docstring
module này khai là lý do tồn tại) là NO-OP VĨNH VIỄN trên dây chuyền thật — luôn báo
PASS "chưa có file kết quả chạy thật" dù file kết quả THẬT đang nằm ngay trên đĩa.

Nguyên tắc viết test: dựng thư mục exports/<study> TẠM (không phụ thuộc fixture
OneDrive-only exports/ZZREB2-.../REFUTE-...), gọi THẲNG evaluate_study(out_dir=...)
với tên file ĐÚNG NHƯ run_stats_analysis.py ghi thật, không grep chuỗi trong mã nguồn.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]


def _nap():
    spec = importlib.util.spec_from_file_location(
        "g6qg_auto06_test", HERE / "tools" / "g6_quality_gate.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["g6qg_auto06_test"] = m
    spec.loader.exec_module(m)
    return m


def _dung_bo_ba_toi_thieu(thu_muc: Path, study: str) -> None:
    """Bộ ba file G6-AUTO-00 đòi — nội dung tối giản, đủ để đọc qua mà không BLOCKED
    sớm ở AUTO-00 (các luật AUTO-01..05 chấp nhận nội dung rỗng/không đọc được)."""
    (thu_muc / f"G6_A7_ANALYSIS_SCRIPTS_{study}.md").write_text(
        "# Script phân tích\n(placeholder)\n", encoding="utf-8")
    (thu_muc / f"G4_A5_SAP_FINAL_{study}.md").write_text(
        "# SAP\n(placeholder)\n", encoding="utf-8")
    (thu_muc / "G6_checkpoint.json").write_text(json.dumps({}), encoding="utf-8")


def _tim_auto06(bao: dict) -> dict:
    for k in bao["checks"]:
        if k["id"] == "G6-AUTO-06":
            return k
    raise AssertionError(f"Không thấy G6-AUTO-06 trong checks: {bao['checks']}")


class TestAuto06BatDuocFileKetQuaThatSu:
    """★★ Ca chính, đúng nguyên văn repro_notes của finding."""

    def test_file_table2_main_outcome_that_khong_co_g5_checkpoint_bi_bat(self):
        m = _nap()
        study = "TEST-AUTO06"
        with tempfile.TemporaryDirectory() as td:
            thu_muc = Path(td)
            _dung_bo_ba_toi_thieu(thu_muc, study)
            # Tên file THẬT do run_stats_analysis.py ghi — KHÔNG chứa "KET_QUA"/
            # "RESULTS", không bắt đầu bằng "stats_output".
            (thu_muc / f"{study}_table2_main_outcome.txt").write_text("x", encoding="utf-8")
            # KHÔNG có G5_checkpoint.json ⇒ chưa từng khoá dữ liệu.
            bao = m.evaluate_study(study, out_dir=thu_muc, write=False)
        chk = _tim_auto06(bao)
        assert chk["pass"] is False, chk
        assert chk["blocking"] is True, chk
        assert "table2_main_outcome" in chk["detail"] or "KHÔNG có G5" in chk["detail"], chk

    def test_cac_ten_file_that_khac_cung_duoc_bat(self):
        """Đối chứng bao phủ: mọi hậu tố THẬT khác mà run_stats_analysis.py ghi ra
        cũng phải được nhận diện — không chỉ đúng một cái tên trong ca chính."""
        m = _nap()
        ten_that = [
            "table1_descriptive.txt", "table3_survival.txt", "table4_multivariate.txt",
            "table5_multiple_imputation.txt", "missing_data_summary.txt",
            "analysis_summary.json", "analysis_syntax.R", "survival_syntax.R",
        ]
        for suffix in ten_that:
            study = "TEST-AUTO06-X"
            with tempfile.TemporaryDirectory() as td:
                thu_muc = Path(td)
                _dung_bo_ba_toi_thieu(thu_muc, study)
                (thu_muc / f"{study}_{suffix}").write_text("x", encoding="utf-8")
                bao = m.evaluate_study(study, out_dir=thu_muc, write=False)
            chk = _tim_auto06(bao)
            assert chk["pass"] is False, f"{suffix}: {chk}"


class TestAuto06KhongBaoDongGiaKhiThatSuChuaCoKetQua:
    """Đối chứng BẮT BUỘC: thư mục KHÔNG có bất kỳ file kết quả thật nào vẫn phải
    PASS như cũ — bản vá không được biến cổng thành báo động giả trên đề tài chưa
    chạy phân tích (tiền đăng ký hợp lệ: script viết trước khi có kết quả)."""

    def test_khong_co_file_ket_qua_van_pass(self):
        m = _nap()
        study = "TEST-AUTO06-CLEAN"
        with tempfile.TemporaryDirectory() as td:
            thu_muc = Path(td)
            _dung_bo_ba_toi_thieu(thu_muc, study)
            bao = m.evaluate_study(study, out_dir=thu_muc, write=False)
        chk = _tim_auto06(bao)
        assert chk["pass"] is True, chk
        assert chk["blocking"] is False, chk


class TestAuto06KetQuaSauKhoaVanPass:
    """Đối chứng: kết quả thật NHƯNG SAU thời điểm khoá G5 (đúng thứ tự an toàn)
    vẫn phải PASS — bản vá không được biến MỌI file kết quả thành lỗi vô điều kiện."""

    def test_ket_qua_sau_g5_checkpoint_van_pass(self):
        import time
        m = _nap()
        study = "TEST-AUTO06-SAU-KHOA"
        with tempfile.TemporaryDirectory() as td:
            thu_muc = Path(td)
            _dung_bo_ba_toi_thieu(thu_muc, study)
            (thu_muc / "G5_checkpoint.json").write_text(json.dumps({}), encoding="utf-8")
            time.sleep(0.05)
            (thu_muc / f"{study}_table2_main_outcome.txt").write_text("x", encoding="utf-8")
            bao = m.evaluate_study(study, out_dir=thu_muc, write=False)
        chk = _tim_auto06(bao)
        assert chk["pass"] is True, chk


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
