"""Công cụ kiểm bản đề cương NỘP HỘI ĐỒNG (G10-T4, 15/10/2026) — `tools/kiem_de_cuong_nop_hoi_dong.py`.

Fixture tự soạn, ngoại tuyến: một đề cương đủ chương, Word dựng từ chính các dòng của .md, biên nhận A12 phủ PMID.
Mỗi luật K1–K7 có một ca hỏng đúng một chỗ. 19/11/2026: chương 5 của fixture mang một hình và một bảng đúng chuẩn
biểu bảng (K9) — fixture cũ để trống chương 5, đúng kiểu bác sĩ chê «biểu bảng chưa có»."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (REPO_ROOT, REPO_ROOT / "tools"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

docx = pytest.importorskip("docx")

import kiem_de_cuong_nop_hoi_dong as K  # noqa: E402

MA = "de-tai-thu"
TOT = """# ĐỀ CƯƠNG NGHIÊN CỨU KHOA HỌC

# 1. ĐẶT VẤN ĐỀ

Thời gian chờ liên quan với hài lòng [1].

# 2. MỤC TIÊU NGHIÊN CỨU

# 3. TỔNG QUAN TÀI LIỆU

# 4. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU

Cỡ mẫu của đề tài là 1.000 phiếu hợp lệ.

| Mã biến | Nội dung |
|---|---|
| thoigian_cho | Thời gian chờ |

## 4.11. Đạo đức trong nghiên cứu

Đề cương chỉ được triển khai sau khi có quyết định phê duyệt của Hội đồng Đạo đức. Người tham gia nhận bản thông tin \
và ký phiếu đồng ý (Phụ lục B). Phiếu chỉ mang mã nghiên cứu (khử định danh); chỉ nhóm nghiên cứu có quyền truy cập; \
số liệu lưu trữ trên máy tính có mật khẩu.

Số quyết định phê duyệt: ……… ngày ……/……/………

# 5. DỰ KIẾN KẾT QUẢ

*Mô tả hình:* sơ đồ các bước chọn đối tượng nghiên cứu.

**Hình 5.1. Sơ đồ chọn đối tượng nghiên cứu (theo STROBE)**

**Bảng 5.1. Mức độ hài lòng chung (Mục tiêu 1)**

| Chỉ số | n/N | Tỷ lệ % | KTC 95% |
|---|---|---|---|
| Hài lòng chung | …/… | … | … – … |

*Ghi chú:* Chữ viết tắt — KTC: khoảng tin cậy.

# 6. KẾ HOẠCH THỰC HIỆN

# 7. TÀI LIỆU THAM KHẢO

1. Tác giả A. Tiêu đề. Tạp chí. 2026. doi:10.1108/IJHCQA-07-2025-0100. PMID: 11111111.

# PHỤ LỤC B. BẢN THÔNG TIN VÀ PHIẾU ĐỒNG Ý THAM GIA NGHIÊN CỨU

# PHỤ LỤC C. PHIẾU THU THẬP SỐ LIỆU

Biến mã hoá ma_ban_kham được ghi ở phụ lục.
"""


def _docx(path: Path, md: str) -> None:
    d = docx.Document()
    for dong in md.splitlines():
        d.add_paragraph(dong.lstrip("#").strip())
    d.save(str(path))


def _dung(tmp: Path, md: str = TOT, docx_md: str | None = None, n: int = 1000, pmid_da_kiem=("11111111",),
          co_docx: bool = True) -> Path:
    (tmp / f"DE_CUONG_NOP_HOI_DONG_{MA}.md").write_text(md, encoding="utf-8", newline="\n")
    if co_docx:
        _docx(tmp / f"DE_CUONG_NOP_HOI_DONG_{MA}.docx", md if docx_md is None else docx_md)
    (tmp / "G3_checkpoint.json").write_text(json.dumps({"confirmed_n": n}), encoding="utf-8", newline="\n")
    (tmp / "A12_RETRACTION_RECEIPT.json").write_text(
        json.dumps({"pmids_checked": list(pmid_da_kiem), "all_clean": True}), encoding="utf-8", newline="\n")
    return tmp


def _ma(loi):
    return {d.split()[0] for d in loi}


def test_de_cuong_tot_dat(tmp_path):
    assert K.kiem(_dung(tmp_path), MA) == []


def test_thieu_tep(tmp_path):
    assert _ma(K.kiem(tmp_path, MA)) == {"K1"}
    assert "K1" in _ma(K.kiem(_dung(tmp_path, co_docx=False), MA))


def test_word_lech_md(tmp_path):
    loi = K.kiem(_dung(tmp_path, docx_md=TOT.replace("# 5. DỰ KIẾN KẾT QUẢ", "")), MA)
    assert _ma(loi) == {"K2"}


def test_thieu_chuong(tmp_path):
    md = TOT.replace("## 4.11. Đạo đức trong nghiên cứu", "## 4.11. Nội dung khác")
    # 21/11/2026: K17 chặn cả bản nháp — mất chương đạo đức thì mất luôn câu «chỉ triển khai sau khi Hội đồng Đạo đức
    # phê duyệt» của chuẩn Việt Nam (TT43/2024) ⇒ hai lỗi, không phải một.
    assert _ma(K.kiem(_dung(tmp_path, md=md), MA)) == {"K3", "K17"}


@pytest.mark.parametrize("chen", ["Kế hoạch này khoá ở cổng G4.", "Xem SAP mục 5.", "Theo §4.6.3.",
                                  "Biến thoigian_cho là phơi nhiễm chính."])
def test_ky_hieu_noi_bo(tmp_path, chen):
    md = TOT.replace("Thời gian chờ liên quan với hài lòng [1].", "Thời gian chờ liên quan với hài lòng [1]. " + chen)
    assert _ma(K.kiem(_dung(tmp_path, md=md), MA)) == {"K4"}


def test_co_mau_lech_g3(tmp_path):
    assert _ma(K.kiem(_dung(tmp_path, n=808), MA)) == {"K5"}


def test_pmid_ngoai_bien_nhan(tmp_path):
    assert _ma(K.kiem(_dung(tmp_path, pmid_da_kiem=("22222222",)), MA)) == {"K6"}


def test_so_dien_thoai(tmp_path):
    md = TOT.replace("Số quyết định phê duyệt", "Điện thoại: 0912 345 678. Số quyết định phê duyệt")
    assert _ma(K.kiem(_dung(tmp_path, md=md), MA)) == {"K7"}


def test_hoi_dong_cong_giao_g10_t4_va_goi_kiem_may(tmp_path):
    import hoi_dong_cong as HD
    nv = next(n for n in HD.NHIEM_VU["G10"] if n["ma"] == "G10-T4")
    assert nv["agent"] == "viet-ban-thao" and nv["dieu_kien"]
    assert set(nv["cham_chuyen_mon"]) == {"tham-dinh-dau-ra", "kiem-chung-trich-dan"}
    assert "DE_CUONG_NOP_HOI_DONG_<mã>.md" in nv["dau_ra"] and "DE_CUONG_NOP_HOI_DONG_<mã>.docx" in nv["dau_ra"]
    ham = HD.KIEM_NHIEM_VU["G10-T4"][1]
    assert ham(_dung(tmp_path), MA) == []
    assert _ma(ham(_dung(tmp_path, n=808), MA)) == {"K5"}
