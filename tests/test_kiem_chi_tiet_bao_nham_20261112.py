# -*- coding: utf-8 -*-
"""kiem_chi_tiet_he_nghien_cuu báo đỏ NHẦM trên đề tài thật BTM (đo 12/11/2026): 3/13 mục 🔴 không phải lỗi.

(1) Bản sao lưu bộ sinh ghi trước khi đè («G0_A1_PICO_FINER_<mã>.bak-YYYYMMDD-HHMMSS.md» của run_g0_auto) bị coi là
    artifact ⇒ «THIẾU bản .docx». (2) docx_theo_cong() xếp MỌI .docx không tiền tố cổng vào G10 (để vẫn soi chuẩn trình
    bày) nên tài liệu làm việc (SOP trích hồ sơ, phiếu thu thập, kế hoạch) bị luật «docx TRÊN ĐĨA dù cổng CHƯA TỪNG
    chạy» báo như thể G10 đã sinh. Luật mồ côi vẫn giữ nguyên cho tài liệu MANG tên cổng / gói nộp; tài liệu làm việc
    vẫn được soi chuẩn trình bày (④). Không PII.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from docx import Document

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import chuan_trinh_bay as C  # noqa: E402
import kiem_chi_tiet_he_nghien_cuu as K  # noqa: E402

MO_COI = "bản .docx TRÊN ĐĨA dù cổng CHƯA TỪNG chạy"


def _run(root: Path, study: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOLS / "kiem_chi_tiet_he_nghien_cuu.py"), "--study", study,
         "--exports-root", str(root), "--no-write", "--khong-canary"],
        capture_output=True, text=True, timeout=300, encoding="utf-8")


def _docx_chuan(p: Path) -> None:
    doc = Document()
    doc.add_paragraph("Nội dung tài liệu " * 20)
    C.ap_dinh_dang_tai_lieu(doc)
    doc.save(p)


def _de_tai(tmp_path: Path, study: str) -> Path:
    d = tmp_path / study
    d.mkdir()
    (d / "G0_checkpoint.json").write_text(json.dumps({"gate": "G0"}), encoding="utf-8", newline="\n")
    return d


def test_nhan_ban_sao_luu():
    assert K.la_ban_sao_luu(Path("G0_A1_PICO_FINER_S.bak-20261025-173629.md"))
    assert K.la_ban_sao_luu(Path("G9_A11_X.bak-20261005-101010.docx"))
    assert not K.la_ban_sao_luu(Path("G0_A1_PICO_FINER_S.md"))
    assert not K.la_ban_sao_luu(Path("G4_A5_SAP_FINAL_S.md.bak-20261014-202242")), "đuôi không phải .md/.docx"


def test_docx_theo_cong_bo_ban_sao_luu(tmp_path):
    for ten in ("G9_A11_X.docx", "G9_A11_X.bak-20261005-101010.docx"):
        (tmp_path / ten).write_bytes(b"x")
    assert [p.name for p in K.docx_theo_cong(tmp_path)["G9"]] == ["G9_A11_X.docx"]


def test_mang_dau_cong():
    assert K.docx_mang_dau_cong("G6", Path("G6a_ANALYSIS_X.docx"))
    assert K.docx_mang_dau_cong("G10", Path("G10_GOI_NOP_X.docx"))
    assert K.docx_mang_dau_cong("G10", Path("DE_CUONG_THONG_NHAT_X.docx"))
    assert not K.docx_mang_dau_cong("G10", Path("SOP_TRICH_HO_SO_X.docx"))
    assert not K.docx_mang_dau_cong("G1", Path("G10_GOI_NOP_X.docx")), "G1 không nhận tệp của G10"


def test_tai_lieu_lam_viec_khong_bi_coi_la_g10_mo_coi_nhung_tai_lieu_cong_van_bi(tmp_path):
    study = "PYTEST-KCT-LAMVIEC"
    d = _de_tai(tmp_path, study)
    for ten in (f"SOP_TRICH_HO_SO_{study}.docx", f"PHIEU_THU_THAP_SO_LIEU_{study}.docx"):
        _docx_chuan(d / ten)
    r = _run(tmp_path, study)
    assert MO_COI not in r.stdout, r.stdout[-3000:]
    assert f"SOP_TRICH_HO_SO_{study}.docx" in r.stdout, "tài liệu làm việc VẪN được soi chuẩn trình bày (④)"
    _docx_chuan(d / f"DE_CUONG_THONG_NHAT_{study}.docx")
    r2 = _run(tmp_path, study)
    assert f"G10: có 1 {MO_COI}" in r2.stdout, r2.stdout[-3000:]
    assert f"DE_CUONG_THONG_NHAT_{study}.docx" in r2.stdout


def test_md_sao_luu_khong_bi_doi_ban_word(tmp_path):
    study = "PYTEST-KCT-BAK"
    d = _de_tai(tmp_path, study)
    (d / f"G0_A1_PICO_FINER_{study}.md").write_text("# G0\n\nNội dung.\n", encoding="utf-8", newline="\n")
    _docx_chuan(d / f"G0_A1_PICO_FINER_{study}.docx")
    bak = f"G0_A1_PICO_FINER_{study}.bak-20261025-173629.md"
    (d / bak).write_text("# G0 cũ\n", encoding="utf-8", newline="\n")
    r = _run(tmp_path, study)
    assert bak not in r.stdout, r.stdout[-3000:]
    (d / f"G0_A1_PICO_FINER_{study}.docx").unlink()
    r2 = _run(tmp_path, study)
    assert f"G0_A1_PICO_FINER_{study}.md: THIẾU bản .docx" in r2.stdout, "artifact thật vẫn bị đòi bản Word"
