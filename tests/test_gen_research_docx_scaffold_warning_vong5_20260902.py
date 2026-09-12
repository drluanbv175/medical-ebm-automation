# -*- coding: utf-8 -*-
"""Vòng rà 5 (2026-09-02), mở rộng task_a5fde306 (2026-07-12): cảnh báo "đây là bản
DỰ THẢO scaffold, KHÔNG phải artifact chính thức" trước đó CHỈ có ở G2 (ethics)/G4
(sap) — G5 (dmp), G8 (review) và G9 (readiness) hoàn toàn KHÔNG cảnh báo, dù cả ba
đều thuộc 6 cổng CỨNG (chữ ký ledger). G9 đặc biệt nguy hiểm: file này là gốc của
phát hiện "bộ sinh G9_READINESS không còn tồn tại" bị sửa sai ở commit af9107a rồi
đính chính ở 9e4aa26 — bài học rút ra là chính đoạn văn bản cảnh báo phải NẰM TRONG
tài liệu sinh ra, không chỉ nằm trong ghi chú audit.

Khác G2/G4 (ledger hash một artifact .md thật — "Variant A"), G5 và G9 ledger hash
CHÍNH checkpoint JSON của cổng đó ("Variant B") — nên câu chữ cảnh báo PHẢI khác,
không được lặp lại nguyên văn "được approve_gate.py hash" (sai với G5/G9). G8 hash
một artifact .md thật (G8_A9_PRESUBMISSION_<study>.md) nên dùng lại đúng khuôn
Variant A của G2/G4.
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
    parts = [p.text for p in d.paragraphs]
    # _tbl() ghi nội dung vào ô bảng (doc.tables), KHÔNG vào doc.paragraphs — phải
    # duyệt riêng để không bỏ sót phần "Mục bảng" (content dạng dict).
    for t in d.tables:
        for row in t.rows:
            for cell in row.cells:
                parts.append(cell.text)
    return "\n".join(parts)


def test_dmp_docx_warns_it_does_not_reflect_real_lock_state():
    study = "TEST-VONG5-DMP"
    d = _study_dir(study)
    try:
        gen = G.ResearchDocxGenerator(study_name=study)
        path = gen.generate("dmp", {})
        text = _doc_text(path)
        assert "DỰ THẢO scaffold" in text
        # Variant B: G5 hash CHECKPOINT, không phải file .md/.docx nào — không được
        # nói "artifact chính thức... được approve_gate.py hash" như G2/G4.
        assert "G5_checkpoint.json" in text
        assert "run_g5_auto.py" in text
        assert "g5_quality_gate.py" in text
    finally:
        _rmtree_retry(d)


def test_review_docx_warns_it_is_not_the_ledger_artifact():
    study = "TEST-VONG5-REVIEW"
    d = _study_dir(study)
    try:
        gen = G.ResearchDocxGenerator(study_name=study)
        path = gen.generate("review", {})
        text = _doc_text(path)
        # Variant A: G8 hash một artifact .md thật, giống hệt khuôn G2/G4.
        assert "KHÔNG phải artifact chính thức" in text
        assert "G8_A9_PRESUBMISSION_" in text
        assert "run_g8_auto.py" in text
        # Không chỉ cảnh báo file sai — còn phải nói rõ nhận xét phản biện THẬT
        # là một artifact khác hẳn, do NGƯỜI viết.
        assert "G8_PEER_REVIEW_REPORT_" in text
    finally:
        _rmtree_retry(d)


def test_readiness_docx_warns_defaults_and_names_the_real_g9_files():
    study = "TEST-VONG5-READINESS"
    d = _study_dir(study)
    try:
        gen = G.ResearchDocxGenerator(study_name=study)
        path = gen.generate("readiness", {})
        text = _doc_text(path)
        assert "DỰ THẢO scaffold" in text
        # Variant B: G9 hash CHECKPOINT, không phải file .docx này.
        assert "G9_checkpoint.json" in text
        assert "run_g10_assemble.py" in text
        # Đúng phát hiện gốc của vòng rà 4 (af9107a → đính chính 9e4aa26): pipeline
        # G9 thật ghi một file HOÀN TOÀN KHÁC — phải nêu tên file đó ra, không để
        # người đọc tưởng "readiness" .docx này là sản phẩm của G9 auto.
        assert "G9_PUBLICATION_READINESS.json" in text
        assert "g9_quality_gate.py" in text
    finally:
        _rmtree_retry(d)


def test_readiness_docx_default_content_is_conservative_not_a_real_measurement():
    # Gọi generate("readiness", {}) — giống hệt cách C1a bị gọi thiếu content thật
    # (phát hiện gốc của vòng rà 4) — verdict phải rơi về NOT READY, không phải một
    # giá trị lạc quan ngẫu nhiên nào khác.
    study = "TEST-VONG5-READINESS-DEFAULT"
    d = _study_dir(study)
    try:
        gen = G.ResearchDocxGenerator(study_name=study)
        path = gen.generate("readiness", {})
        text = _doc_text(path)
        assert "KẾT LUẬN NGHIỆM THU: NOT READY" in text
        # _save() chạy chuan_trinh_bay.ap_dinh_dang_tai_lieu() để làm sạch ký tự
        # trang trí trước khi lưu — "🔴" trong content mặc định trở thành nhãn chữ
        # "[Nghiêm trọng]", không còn emoji nguyên văn trong .docx đã lưu.
        assert "[Nghiêm trọng] CHƯA ĐÓNG" in text
    finally:
        _rmtree_retry(d)


def test_none_of_the_three_scaffold_filenames_collide_with_real_ledger_artifacts():
    # Bất biến CỐT LÕI kế thừa từ task_a5fde306: KHÔNG đổi tên file scaffold để
    # "khớp" tên artifact thật — nguy cơ ghi đè nhầm bản đã khóa. Khóa cả 3 tên mới.
    study = "TEST-VONG5-NAME"
    d = _study_dir(study)
    try:
        gen = G.ResearchDocxGenerator(study_name=study)

        dmp_path = Path(gen.generate("dmp", {}))
        assert dmp_path.name == f"G5b_DMP_{study}.docx"
        assert dmp_path.name != f"G5_A6_DATA_MGMT_{study}.docx"

        review_path = Path(gen.generate("review", {}))
        assert review_path.name == f"G8_REVIEW_{study}.docx"
        assert review_path.name != f"G8_A9_PRESUBMISSION_{study}.docx"

        readiness_path = Path(gen.generate("readiness", {}))
        assert readiness_path.name == f"G9_READINESS_{study}.docx"
        # G9 thật không có sản phẩm .docx nào cùng gốc tên để va — vẫn chốt tên để
        # hồi quy nếu sau này ai đó đổi.
        assert readiness_path.name != "G9_PUBLICATION_READINESS.json"
    finally:
        _rmtree_retry(d)


def test_render_kv_body_refactor_keeps_generic_flag_behavior_identical():
    # 2026-09-02: _gen_generic() được tách phần thân sang _render_kv_body() để
    # _gen_review() dùng lại — hồi quy hành vi CŨ (content rỗng → gắn cờ nhắc điền,
    # không phải im lặng bỏ qua) phải còn nguyên sau khi tách.
    study = "TEST-VONG5-GENERIC-REFACTOR"
    d = _study_dir(study)
    try:
        gen = G.ResearchDocxGenerator(study_name=study)
        path = gen.generate("some-unmapped-key-outside-artifact-map", {})
        text = _doc_text(path)
        assert "Chủ nhiệm điền nội dung cho phần này." in text
    finally:
        _rmtree_retry(d)


def test_render_kv_body_refactor_still_renders_list_and_dict_sections():
    study = "TEST-VONG5-GENERIC-REFACTOR-CONTENT"
    d = _study_dir(study)
    try:
        gen = G.ResearchDocxGenerator(study_name=study)
        content = {
            "Mục danh sách": ["mục a", "mục b"],
            "Mục bảng": {"cột 1": "giá trị 1"},
            "Mục văn bản": "một đoạn văn bản",
        }
        path = gen.generate("some-unmapped-key-outside-artifact-map-2", content)
        text = _doc_text(path)
        assert "mục a" in text
        assert "mục b" in text
        assert "cột 1" in text
        assert "giá trị 1" in text
        assert "một đoạn văn bản" in text
    finally:
        _rmtree_retry(d)
