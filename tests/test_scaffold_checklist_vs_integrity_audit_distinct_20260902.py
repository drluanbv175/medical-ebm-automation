# -*- coding: utf-8 -*-
"""Vòng rà 6 (2026-09-02, kiểm chi tiết hệ nghiên cứu): SCAFFOLD_FILES hàng "19"
(Research_Integrity_Audit.md — kiểm toán completeness A1-A18) từng dùng CHUNG
artifact_key "checklist" với hàng "17" (Reporting_Checklist.md — bảng chuẩn báo
cáo CONSORT/STROBE/PRISMA). Khác 2 cặp trùng khóa còn lại trong SCAFFOLD_FILES
("literature" ở hàng 03/04, "sap" ở hàng 11/15) — CẢ HAI đó có chủ ý, tiêu đề/nội
dung artifact trong ARTIFACT_MAP đã gộp cả hai khái niệm nên gọi generate() hai
lần cho cùng khóa vẫn ra đúng một nội dung — cặp "checklist" KHÔNG có sự gộp
tương tự: tiêu đề của khóa chỉ nói CONSORT/STROBE/PRISMA, không hề nhắc
completeness audit.

Hệ quả đo được trước khi vá (bằng `scaffold()` thật, không giả lập):
- STUDY_INDEX.md ghi CÙNG tên .docx kỳ vọng cho 2 hàng 17/19 khác nội dung.
- generate("checklist") gọi lần 2 (từ hàng 19, chạy SAU hàng 17 trong vòng lặp)
  ghi đè .docx của hàng 17 trên đĩa — mất tên file distinct dù cả hai hiện đang
  chỉ là khung rỗng (content=None → _gen_generic → cùng "flag" placeholder).

Đã vá: thêm khóa "integrity-audit" (G9b) riêng cho hàng 19; ARTIFACT_MAP tăng
38 → 39. Test này khóa hành vi: hai hàng phải sinh HAI TÊN FILE .docx khác nhau,
và STUDY_INDEX.md không còn ghi trùng tên cho 2 hàng.
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

pytest.importorskip("docx", reason="python-docx chưa cài — bỏ qua test sinh .docx thật")

import gen_research_docx as G  # noqa: E402
import scaffold_research_project as S  # noqa: E402


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


class TestScaffoldFilesRowsUseDistinctKeys:
    def test_row_17_and_row_19_have_different_artifact_keys(self):
        row17 = next(r for r in S.SCAFFOLD_FILES if r[0] == "17")
        row19 = next(r for r in S.SCAFFOLD_FILES if r[0] == "19")
        assert row17[1] == "Reporting_Checklist"
        assert row19[1] == "Research_Integrity_Audit"
        assert row17[3] == "checklist"
        assert row19[3] == "integrity-audit", (
            "hàng 19 lại dùng chung khóa với hàng 17 — hồi quy lỗi vòng rà 6"
        )

    def test_new_key_registered_with_own_unique_code(self):
        assert "integrity-audit" in G.ARTIFACT_MAP
        code, gate, title = G.ARTIFACT_MAP["integrity-audit"]
        assert code == "G9b"
        assert code != G.ARTIFACT_MAP["checklist"][0]
        assert "checklist" not in title.lower() or "audit" in title.lower()
        # Không được trùng mã với BẤT KỲ khóa nào khác trong danh mục.
        codes = [v[0] for v in G.ARTIFACT_MAP.values()]
        assert codes.count(code) == 1


class TestScaffoldProducesTwoDistinctDocxFiles:
    def test_scaffold_generates_two_different_docx_names_for_17_and_19(self):
        study = "TEST-VONG6-CHECKLIST-DISTINCT"
        d = _study_dir(study)
        try:
            S.scaffold(study, with_docx=True)
            files = {p.name for p in d.iterdir()}
            checklist_docx = f"{G.ARTIFACT_MAP['checklist'][0]}_CHECKLIST_{study}.docx"
            integrity_docx = f"{G.ARTIFACT_MAP['integrity-audit'][0]}_INTEGRITY-AUDIT_{study}.docx"
            assert checklist_docx in files, f"thiếu {checklist_docx} trong {sorted(files)}"
            assert integrity_docx in files, f"thiếu {integrity_docx} trong {sorted(files)}"
            assert checklist_docx != integrity_docx
        finally:
            _rmtree_retry(d)

    def test_both_source_md_files_still_have_their_own_distinct_real_content(self):
        # Bất biến: dù .docx từng bị đè, các file .md (nội dung THẬT mà cổng đọc)
        # chưa bao giờ bị ảnh hưởng — num/fname không đổi qua bản vá này.
        study = "TEST-VONG6-CHECKLIST-MD-CONTENT"
        d = _study_dir(study)
        try:
            S.scaffold(study, with_docx=True)
            checklist_md = (d / "17_Reporting_Checklist.md").read_text(encoding="utf-8")
            integrity_md = (d / "19_Research_Integrity_Audit.md").read_text(encoding="utf-8")
            assert "CONSORT" in checklist_md
            assert "Kiểm toán completeness A1" in integrity_md
            assert checklist_md != integrity_md
        finally:
            _rmtree_retry(d)


class TestStudyIndexNoLongerAliasesTwoRows:
    def test_study_index_lists_two_different_expected_docx_names(self):
        study = "TEST-VONG6-CHECKLIST-INDEX"
        d = _study_dir(study)
        try:
            S.scaffold(study, with_docx=True)
            index_text = (d / "STUDY_INDEX.md").read_text(encoding="utf-8")
            row17_line = next(
                ln for ln in index_text.splitlines() if ln.strip().startswith("| 17 ")
            )
            row19_line = next(
                ln for ln in index_text.splitlines() if ln.strip().startswith("| 19 ")
            )
            checklist_docx = f"{G.ARTIFACT_MAP['checklist'][0]}_CHECKLIST_{study}.docx"
            integrity_docx = f"{G.ARTIFACT_MAP['integrity-audit'][0]}_INTEGRITY-AUDIT_{study}.docx"
            assert checklist_docx in row17_line
            assert integrity_docx in row19_line
            assert row17_line != row19_line
        finally:
            _rmtree_retry(d)
