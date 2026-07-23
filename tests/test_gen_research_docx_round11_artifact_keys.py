# -*- coding: utf-8 -*-
"""Hồi quy vòng lặp kiểm tra-hoàn thiện vòng 11 (2026-07-23, workflow đối kháng
wf_37b290b2-31e, dimension research_agents_deep_audit + g6_g7_depth_and_artifact_map):

10 agent doctrine khai `--artifact <khóa>` bằng khóa KHÔNG tồn tại trong
ARTIFACT_MAP (nghien-cuu-dinh-tinh.md, mo-hinh-tien-luong.md, kinh-te-y-te.md,
an-toan-nghien-cuu.md, khoang-trong-nghien-cuu.md, trich-xuat-y-van.md,
tham-dinh-phe-binh.md, kiem-chung-trich-dan.md, huong-dan-lam-sang.md,
so-cai-ghi-nho.md) — generate() rơi vào fallback code="GX"/gate="" (mất định
danh cổng G0-G9), cùng lớp lỗi đã vá cho co-mau-nghien-cuu.md/meta-phan-tich.md/
cong-cu-do-luong.md ở các vòng trước (xem test_gen_research_docx_gate_and_
instrument_key.py). Thêm đúng 10 khóa vào ARTIFACT_MAP — kiểm ở đây mỗi khóa
sinh đúng mã cổng, không rơi vào generic.

Đồng thời hồi quy thu-thu-tai-lieu.md: đã sửa lệnh mẫu từ khóa bịa
`literature-list` sang khóa thật `literature` (dùng lại G0c, không cần khóa mới).
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


NEW_KEYS_AND_CODES = [
    ("research-gap", "G0d"),
    ("extraction", "G0e"),
    ("critical-appraisal", "G0f"),
    ("qualitative-design", "G1e"),
    ("safety-monitoring", "G2a"),
    ("prediction-model", "G6c"),
    ("clinical-guideline", "G6d"),
    ("health-economics", "G7c"),
    ("citation-check", "G7d"),
    ("study-log", "G9a"),
]


class TestRound11NewArtifactKeys:
    def test_each_new_key_present_in_artifact_map(self):
        for key, code in NEW_KEYS_AND_CODES:
            assert key in G.ARTIFACT_MAP, f"{key} thiếu trong ARTIFACT_MAP"
            assert G.ARTIFACT_MAP[key][0] == code

    def test_each_new_key_generates_with_correct_code_not_generic(self, capsys):
        for key, code in NEW_KEYS_AND_CODES:
            d = _study_dir(f"TEST-VONG11-{key.upper()}")
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

    def test_no_code_collision_with_existing_22_keys(self):
        """32 khóa nghiên cứu (22 cũ + 10 mới vòng 11) + 4 khóa lâm sàng (vòng
        15, xem test_gen_research_docx_round15_clinical_artifact_keys.py) =
        36 — phải có mã code riêng biệt, không trùng."""
        codes = [v[0] for v in G.ARTIFACT_MAP.values()]
        assert len(codes) == len(set(codes)), "Có mã artifact_code bị trùng trong ARTIFACT_MAP"
        assert len(G.ARTIFACT_MAP) == 36


class TestThuThuTaiLieuLiteratureListFix:
    def test_doctrine_no_longer_references_bogus_literature_list(self):
        doctrine = (
            REPO_ROOT.parent / ".claude" / "agents" / "thu-thu-tai-lieu.md"
        )
        if not doctrine.exists():
            doctrine = REPO_ROOT / ".claude" / "agents" / "thu-thu-tai-lieu.md"
        assert doctrine.exists(), "Không tìm thấy thu-thu-tai-lieu.md ở root hay mirror"
        text = doctrine.read_text(encoding="utf-8")
        assert "--artifact literature-list" not in text
        assert "--artifact literature" in text

    def test_literature_key_still_maps_to_g0c(self, capsys):
        d = _study_dir("TEST-VONG11-LITERATURE-REUSE")
        try:
            gen = G.ResearchDocxGenerator(study_name=d.name)
            path = gen.generate("literature", {})
            assert re.search(r"G0c_LITERATURE_", path, re.IGNORECASE)
            captured = capsys.readouterr()
            assert "ngoài danh mục nghiên cứu chuẩn" not in captured.out
        finally:
            _rmtree_retry(d)
