# -*- coding: utf-8 -*-
"""Hồi quy vòng lặp kiểm tra-hoàn thiện vòng 15 (2026-07-24, dimension
workflow_agents_a):

4 agent LÂM SÀNG (quyet-dinh-chung.md, loi-dan-tuan-thu.md, ket-qua-hoc-tap.md,
cap-nhat-guideline.md) khai `--artifact <khóa>` bằng khóa KHÔNG tồn tại trong
ARTIFACT_MAP (shared-decision/patient-instructions/outcome-learning/
guideline-update) — cùng lớp lỗi "mất định danh cổng, rơi về generic GX" đã vá
cho 10 khóa NGHIÊN CỨU ở vòng 11 (xem test_gen_research_docx_round11_artifact_
keys.py). Khác biệt: 4 khóa này là Cổng A/B lâm sàng, KHÔNG thuộc chuỗi G0-G9
nghiên cứu — trường "gate" ghi "A"/"B" thay vì "G_".
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


CLINICAL_KEYS_CODES_AND_GATES = [
    ("shared-decision", "CA1", "A"),
    ("patient-instructions", "CA2", "A"),
    ("outcome-learning", "CB1", "B"),
    ("guideline-update", "CB2", "B"),
]


class TestRound15ClinicalArtifactKeys:
    def test_each_clinical_key_present_in_artifact_map_with_ab_gate(self):
        for key, code, gate in CLINICAL_KEYS_CODES_AND_GATES:
            assert key in G.ARTIFACT_MAP, f"{key} thiếu trong ARTIFACT_MAP"
            assert G.ARTIFACT_MAP[key][0] == code
            assert G.ARTIFACT_MAP[key][1] == gate, (
                f"{key} phải gắn Cổng A/B lâm sàng, không phải cổng G0-G9 nghiên cứu"
            )

    def test_each_clinical_key_generates_with_correct_code_not_generic(self, capsys):
        for key, code, _gate in CLINICAL_KEYS_CODES_AND_GATES:
            d = _study_dir(f"TEST-VONG15-{key.upper()}")
            try:
                gen = G.ResearchDocxGenerator(study_name=d.name)
                path = gen.generate(key, {})
                assert re.search(rf"{re.escape(code)}_{re.escape(key.upper())}_", path, re.IGNORECASE), (
                    f"{key} không sinh đúng mã {code}: {path}"
                )
                captured = capsys.readouterr()
                assert "ngoài danh mục nghiên cứu chuẩn" not in captured.out, (
                    f"{key} vẫn rơi vào fallback generic (cảnh báo còn xuất hiện)"
                )
            finally:
                _rmtree_retry(d)

    def test_no_code_collision_between_clinical_and_research_keys(self):
        codes = [v[0] for v in G.ARTIFACT_MAP.values()]
        assert len(codes) == len(set(codes)), "Có mã artifact_code bị trùng trong ARTIFACT_MAP"


ROUND16_CLINICAL_KEYS_CODES_AND_GATES = [
    ("evidence-search", "CA3", "A"),
    ("clinical-case-summary", "CA4", "A-B"),
]


class TestRound16ClinicalArtifactKeys:
    """Hồi quy vòng lặp kiểm tra-hoàn thiện vòng 16 (2026-07-24): 2 khóa bị
    bỏ sót ở đợt vá vòng 15 cùng ngày (tra-cuu-chung-cu.md dùng
    'evidence-search'; dieu-phoi-lam-sang.md — agent điều phối chính, dùng
    'clinical-case-summary' ở bước CUỐI CÙNG sau Cổng B)."""

    def test_each_key_present_with_ab_gate(self):
        for key, code, gate in ROUND16_CLINICAL_KEYS_CODES_AND_GATES:
            assert key in G.ARTIFACT_MAP, f"{key} thiếu trong ARTIFACT_MAP"
            assert G.ARTIFACT_MAP[key][0] == code
            assert G.ARTIFACT_MAP[key][1] == gate

    def test_each_key_generates_with_correct_code_not_generic(self, capsys):
        for key, code, _gate in ROUND16_CLINICAL_KEYS_CODES_AND_GATES:
            d = _study_dir(f"TEST-VONG16-{key.upper()}")
            try:
                gen = G.ResearchDocxGenerator(study_name=d.name)
                path = gen.generate(key, {})
                assert re.search(rf"{re.escape(code)}_{re.escape(key.upper())}_", path, re.IGNORECASE), (
                    f"{key} không sinh đúng mã {code}: {path}"
                )
                captured = capsys.readouterr()
                assert "ngoài danh mục nghiên cứu chuẩn" not in captured.out
            finally:
                _rmtree_retry(d)
