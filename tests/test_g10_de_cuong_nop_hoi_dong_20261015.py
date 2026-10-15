"""Bản đề cương NỘP HỘI ĐỒNG trong gói phát hành G10 (15/10/2026).

Bối cảnh: đề tài C1a nộp Hội đồng một đề cương viết lại bằng văn phong khoa học (`DE_CUONG_NOP_HOI_DONG_<mã>.md/.docx`),
trong khi manifest G10 chỉ ràng buộc bản lắp máy `DE_CUONG_THONG_NHAT_<mã>` — chữ ký G10 không phủ văn bản thật sự nộp.
Kiểm: (1) có tệp thì cả cặp vào manifest, thiếu nửa ⇒ fail-closed; (2) quét nhãn [CẦN…]/PII liên lạc trên bản nộp nhưng
không coi DOI là số điện thoại và không coi dòng chấm «………» là ô trống; (3) PMID của bản nộp vào phạm vi A12.
Ngoại tuyến, văn bản fixture tự soạn.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (REPO_ROOT, REPO_ROOT / "tools"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

docx = pytest.importorskip("docx")

import g10_quality_gate as G  # noqa: E402
import run_g10_assemble as A  # noqa: E402

MA = "de-tai-thu"
SACH = ("# ĐỀ CƯƠNG\n\nSố quyết định phê duyệt: ……… ngày ……/……/………\n\n"
        "1. Tác giả A. Tiêu đề. Tạp chí. 2026. doi:10.1108/IJHCQA-07-2025-0100. PMID: 11111111.\n")


def _docx(path: Path, chu: str) -> None:
    d = docx.Document()
    for dong in chu.splitlines():
        d.add_paragraph(dong)
    d.save(str(path))


def _goi(tmp: Path, nop_md: str | None = SACH, nop_docx: str | None = SACH) -> dict:
    (tmp / f"DE_CUONG_THONG_NHAT_{MA}.md").write_text("# Đề cương lắp\n\nPMID: 22222222.\n", encoding="utf-8",
                                                     newline="\n")
    _docx(tmp / f"DE_CUONG_THONG_NHAT_{MA}.docx", "Đề cương lắp")
    (tmp / f"GOI_QUYET_DINH_{MA}.md").write_text("# Gói quyết định\n", encoding="utf-8", newline="\n")
    if nop_md is not None:
        (tmp / f"DE_CUONG_NOP_HOI_DONG_{MA}.md").write_text(nop_md, encoding="utf-8", newline="\n")
    if nop_docx is not None:
        _docx(tmp / f"DE_CUONG_NOP_HOI_DONG_{MA}.docx", nop_docx)
    files, _ = G._package_files(MA, tmp, {})
    return files


def _sach(files: dict) -> tuple[bool, str]:
    giu = {k: files[k] for k in ("final_protocol_md", "final_protocol_docx", "decision_package",
                                 "irb_protocol_md", "irb_protocol_docx") if k in files}
    ok, chung_cu, _ = G._documents_clean(giu)
    return ok, chung_cu


def test_khong_co_ban_nop_thi_manifest_nhu_cu(tmp_path):
    files = _goi(tmp_path, nop_md=None, nop_docx=None)
    assert "irb_protocol_md" not in files and "irb_protocol_docx" not in files
    assert _sach(files)[0]


def test_co_ban_nop_thi_ca_cap_vao_manifest_va_sach(tmp_path):
    files = _goi(tmp_path)
    assert files["irb_protocol_md"].name == f"DE_CUONG_NOP_HOI_DONG_{MA}.md"
    assert files["irb_protocol_docx"].name == f"DE_CUONG_NOP_HOI_DONG_{MA}.docx"
    ok, chung_cu = _sach(files)
    assert ok, chung_cu  # dòng chấm «………» và DOI có dạng số không bị coi là ô trống/số điện thoại
    man = G._manifest(tmp_path, files)
    assert man["files"]["irb_protocol_md"]["sha256"] and man["files"]["irb_protocol_docx"]["sha256"]


def test_thieu_nua_cap_thi_fail_closed(tmp_path):
    files = _goi(tmp_path, nop_docx=None)
    assert "irb_protocol_docx" in files
    ok, chung_cu = _sach(files)
    assert not ok and "missing_or_unreadable" in chung_cu and "irb_protocol_docx" in chung_cu


@pytest.mark.parametrize("ban_loi, khoa", [
    (SACH + "\nĐiện thoại liên hệ: 0912 345 678\n", "contact_pii"),
    (SACH + "\nEmail: nguoi.thu@example.com\n", "contact_pii"),
    (SACH + "\nMã đăng ký: [CẦN BỔ SUNG]\n", "placeholders"),
])
def test_ban_nop_co_loi_bi_bat_ca_md_lan_docx(tmp_path, ban_loi, khoa):
    files = _goi(tmp_path, nop_md=ban_loi, nop_docx=ban_loi)
    ok, chung_cu = _sach(files)
    assert not ok
    phan = chung_cu.split(f"{khoa}=")[1].split(";")[0]
    assert "irb_protocol_md" in phan and "irb_protocol_docx" in phan


def test_pmid_ban_nop_vao_pham_vi_a12(tmp_path):
    _goi(tmp_path)
    assert A._extract_pmids_from_final_document(MA, tmp_path) == {"11111111", "22222222"}
    assert "10.1108/IJHCQA-07-2025-0100" in A._scan_doi_citation_coverage("", MA, tmp_path)
