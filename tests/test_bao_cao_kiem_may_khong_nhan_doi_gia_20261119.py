"""Hồi quy 19/11/2026 — báo cáo kiểm bằng máy (G0-T3/T4 và A12 nội dung) không được tự sinh «DOI sai định dạng».

Kiểm toàn diện 19/11/2026: `verify_exports_integrity.py` (chế độ quét đủ) báo 7 LỖI CHẶN EXP-DOI-FORMAT ở thư mục
`kiem_may_api/` của C1a và BTM. Không có DOI nào sai — câu ghi chú cố định ở đầu báo cáo «bài chỉ có DOI: Europe
PMC/Crossref» bị luật `_DOI_BAD` (nhãn «doi:» đứng trước một chuỗi không bắt đầu bằng «10.») đọc thành một DOI sai.
Luật đúng (bắt ô DOI bịa/gõ nhầm); câu văn của bộ sinh mới là chỗ sai. Ai commit thư mục `kiem_may_api/` sẽ bị chặn oan.

Phép kiểm dựng báo cáo bằng ĐÚNG đường chạy của hai công cụ (khách API giả, abstract giả) rồi cho bộ kiểm liêm chính
đọc — không chép lại chuỗi để so.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import kiem_noi_dung_trich_dan as KND  # noqa: E402
import kiem_tong_quan_g0_api as K  # noqa: E402
import verify_exports_integrity as VEI  # noqa: E402

from tests import test_api_claude_nghien_cuu_20261117 as TA  # noqa: E402
from tests import test_kiem_tong_quan_g0_api_20261118 as TK  # noqa: E402


def _loi_dinh_danh(md: Path) -> list:
    rep = VEI.Report()
    VEI._check_source_format(md, md.read_text(encoding="utf-8").splitlines(), rep)
    return [f"{f.code}:{f.line} {f.message}" for f in rep.findings]


def test_bao_cao_kiem_tong_quan_g0_khong_bi_bao_doi_sai(tmp_path):
    goc = TK._goc(tmp_path)
    K.main(["--study", TK.S, "--goi-api"], client=TK.Khach(TK._a_dat, TK._b_dat, TK.C_RONG), goc=goc,
           lay=lambda p: TK.ABS, lay_doi=lambda d: TK.ABS_DOI)
    md = goc / "exports" / TK.S / "kiem_may_api" / f"G0_KIEM_TONG_QUAN_{TK.S}.md"
    assert md.is_file()
    assert _loi_dinh_danh(md) == []


def test_bao_cao_a12_kiem_noi_dung_khong_bi_bao_doi_sai(tmp_path):
    goc = TA._goc_tam(tmp_path)
    KND.main(["--study", "S1", "--goi-api"], client=TA.KhachGia(TA._tra_knd), lay=lambda p: TA.ABS, goc=goc)
    md = goc / "exports" / "S1" / "kiem_may_api" / "A12_KIEM_NOI_DUNG_S1.md"
    assert md.is_file()
    assert _loi_dinh_danh(md) == []


def test_luat_doi_van_bat_o_doi_bia(tmp_path):
    """Không nới luật: một ô «DOI: chưa có» thật vẫn bị bắt."""
    md = tmp_path / "x.md"
    md.write_text("| 1 | Bài A | DOI: chua-co |\n", encoding="utf-8", newline="\n")
    assert any(x.startswith("EXP-DOI-FORMAT") for x in _loi_dinh_danh(md))


# ── Đề cương nộp (luật K8) không bị đòi nhãn «Cần bác sĩ kiểm chứng» ─────────────────────────────────────────────
def _canh_bao_nhan(p: Path) -> list:
    rep = VEI.Report()
    VEI._check_disclaimer(p, p.read_text(encoding="utf-8"), rep)
    return [f.code for f in rep.findings]


def test_de_cuong_nop_dung_k8_khong_bi_doi_nhan(tmp_path):
    import kiem_de_cuong_nop_hoi_dong as KDC  # noqa: PLC0415

    p = tmp_path / "DE_CUONG_NOP_HOI_DONG_S1.md"
    p.write_text("# ĐỀ CƯƠNG NGHIÊN CỨU\n\nNội dung đề cương hoàn chỉnh.\n", encoding="utf-8", newline="\n")
    assert KDC.loi_k8(p.read_text(encoding="utf-8")) == []
    assert _canh_bao_nhan(p) == []


def test_tai_lieu_noi_bo_khac_thieu_nhan_van_bi_canh_bao(tmp_path):
    p = tmp_path / "G4_A5_SAP_FINAL_S1.md"
    p.write_text("# SAP\n\nNội dung.\n", encoding="utf-8", newline="\n")
    assert _canh_bao_nhan(p) == ["EXP-NO-DISCLAIMER"]
