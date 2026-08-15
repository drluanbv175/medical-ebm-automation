# -*- coding: utf-8 -*-
"""Hồi quy 2 phát hiện từ vòng lặp kiểm tra-hoàn thiện vòng 9 (2026-07-22,
workflow đối kháng wf_110cffc4-258, dimension docx_pipeline_and_remaining_ebm_master_tools):

1. generate_all_gates() trước đây trả về list RỖNG hoàn toàn im lặng khi `gate`
   không khớp bất kỳ artifact nào (sai hoa/thường như "g3", hoặc cổng không tồn
   tại như "G10") — main() không kiểm tra rỗng, nên `--gate` sai thoát mã 0,
   không sinh file, không cảnh báo, mâu thuẫn với chính docstring "fail-soft,
   không im lặng" của generate().
2. cong-cu-do-luong.md dùng khóa artifact bịa "measurement-tool" thay vì
   "instrument" đúng chuẩn trong ARTIFACT_MAP (cùng lớp lỗi đã vá cho
   co-mau-nghien-cuu.md/meta-phan-tich.md ở vòng trước) — kiểm ở đây bằng cách
   xác nhận "instrument" sinh đúng còn "measurement-tool" rơi vào nhánh generic
   kèm cảnh báo (không phải generator riêng của G3d).
"""
from __future__ import annotations

import re
import shutil
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import gen_research_docx as G  # noqa: E402


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
    return d


class TestGenerateAllGatesSilentFailure:
    def test_nonexistent_gate_returns_empty_and_warns(self, capsys):
        d = _study_dir("TEST-VONG9-GATE-G10")
        try:
            gen = G.ResearchDocxGenerator(study_name=d.name)
            results = gen.generate_all_gates("G10", {})
            assert results == []
            captured = capsys.readouterr()
            assert "không khớp bất kỳ artifact nào" in captured.out
            assert "Cổng hợp lệ" in captured.out
        finally:
            _rmtree_retry(d)

    def test_wrong_case_gate_returns_empty_and_warns(self, capsys):
        d = _study_dir("TEST-VONG9-GATE-LOWERCASE")
        try:
            gen = G.ResearchDocxGenerator(study_name=d.name)
            results = gen.generate_all_gates("g3", {})
            assert results == []
            captured = capsys.readouterr()
            assert "không khớp bất kỳ artifact nào" in captured.out
        finally:
            _rmtree_retry(d)

    def test_correct_case_gate_still_generates_files(self, capsys):
        d = _study_dir("TEST-VONG9-GATE-G3-VALID")
        try:
            gen = G.ResearchDocxGenerator(study_name=d.name)
            results = gen.generate_all_gates("G3", {})
            assert len(results) == 4  # samplesize, variables, crf, instrument
            captured = capsys.readouterr()
            assert "không khớp bất kỳ artifact nào" not in captured.out
        finally:
            _rmtree_retry(d)


class TestInstrumentArtifactKey:
    def test_instrument_key_maps_to_g3d_not_generic(self, capsys):
        d = _study_dir("TEST-VONG9-INSTRUMENT-KEY")
        try:
            gen = G.ResearchDocxGenerator(study_name=d.name)
            path = gen.generate("instrument", {})
            assert re.search(r"G3d_INSTRUMENT_", path, re.IGNORECASE)
            captured = capsys.readouterr()
            assert "ngoài danh mục nghiên cứu chuẩn" not in captured.out
        finally:
            _rmtree_retry(d)

    def test_bogus_measurement_tool_key_falls_back_to_generic_with_warning(self, capsys):
        d = _study_dir("TEST-VONG9-MEASUREMENT-TOOL-BOGUS")
        try:
            gen = G.ResearchDocxGenerator(study_name=d.name)
            path = gen.generate("measurement-tool", {})
            assert "GX_MEASUREMENT-TOOL_" in path
            captured = capsys.readouterr()
            assert "ngoài danh mục nghiên cứu chuẩn" in captured.out
        finally:
            _rmtree_retry(d)
