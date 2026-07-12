# -*- coding: utf-8 -*-
"""Hồi quy task_a5fde306 (rà kiến trúc 2026-07-12): gen_research_docx.py sinh artifact
G2 (ethics)/G4 (sap) tên KHÁC file mà cổng khóa chống p-hacking (run_g6_auto.py::
_ledger_approved) thật sự đọc/hash (G2_A3_ETHICS_PACKAGE_<study>.md /
G4_A5_SAP_FINAL_<study>.md do run_g2_auto.py/run_g4_auto.py sinh). Đổi tên .docx ở đây
để "khớp" có nguy cơ ghi đè nhầm bản thật đã khóa bằng bản DỰ THẢO — nên bản vá KHÔNG đổi
tên file, chỉ thêm cảnh báo tường minh trong tài liệu sinh ra. Test này khóa lại hành vi đó.
"""
from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

docx = pytest.importorskip("docx", reason="python-docx chưa cài — bỏ qua test sinh .docx thật")

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


def _doc_text(path: str) -> str:
    d = docx.Document(path)
    return "\n".join(p.text for p in d.paragraphs)


def test_ethics_docx_warns_it_is_not_the_ledger_artifact():
    study = "TEST-A5FDE306-ETHICS"
    d = _study_dir(study)
    try:
        gen = G.ResearchDocxGenerator(study_name=study)
        path = gen.generate("ethics", {})
        text = _doc_text(path)
        assert "KHÔNG phải artifact chính thức" in text
        assert "G2_A3_ETHICS_PACKAGE_" in text
        assert "run_g2_auto.py" in text
    finally:
        _rmtree_retry(d)


def test_sap_docx_warns_it_is_not_the_ledger_artifact():
    study = "TEST-A5FDE306-SAP"
    d = _study_dir(study)
    try:
        gen = G.ResearchDocxGenerator(study_name=study)
        path = gen.generate("sap", {})
        text = _doc_text(path)
        assert "KHÔNG phải artifact chính thức" in text
        assert "G4_A5_SAP_FINAL_" in text
        assert "run_g4_auto.py" in text
    finally:
        _rmtree_retry(d)


def test_ethics_docx_filename_unchanged_does_not_collide_with_ledger_artifact_name():
    # Bất biến CỐT LÕI của bản vá: KHÔNG đổi tên để "khớp" Scheme B — nếu ai đó sau
    # này vô tình đổi lại, test này sẽ bắt hồi quy (nguy cơ ghi đè nhầm bản đã khóa).
    study = "TEST-A5FDE306-NAME"
    d = _study_dir(study)
    try:
        gen = G.ResearchDocxGenerator(study_name=study)
        path = Path(gen.generate("ethics", {}))
        assert path.name == f"G2_ETHICS_{study}.docx"
        assert path.name != f"G2_A3_ETHICS_PACKAGE_{study}.docx"
    finally:
        _rmtree_retry(d)


def test_module_docstring_init_example_matches_real_signature():
    # 2026-07-12: docstring cũ ví dụ gọi ResearchDocxGenerator(study_name=..., gate=...)
    # nhưng __init__ thật không nhận `gate` -> TypeError nếu copy-paste. Khóa hồi quy.
    import inspect
    sig = inspect.signature(G.ResearchDocxGenerator.__init__)
    assert "gate" not in sig.parameters
    assert "study_name" in sig.parameters
