# -*- coding: utf-8 -*-
"""Kiểm bản thảo gửi Tạp chí Y Dược Thực hành 175 theo thể lệ + bảng gọn của hồ sơ tạp chí (19/11/2026).

Ca thật: gói nộp đề tài BTM đo bằng Word được 15 trang (thể lệ ≤ 10 trang kể cả tài liệu tham khảo), từ khoá phân cách
bằng dấu chấm phẩy (thể lệ: dấu phẩy), nhãn «BẢN NHÁP AI» và ghi chú «>» nằm ngay trong bản thảo. Bảng chia cột đều làm
cột đầu xuống dòng liên tục — bảng gọn (cột theo nội dung) đưa bản thảo từ 13 xuống 12 trang.
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import kiem_ban_thao_tap_chi as KB  # noqa: E402
import md2docx_vn as M2D  # noqa: E402

TEN = "Tạp chí Y Dược Thực hành 175"
GH = KB.GIOI_HAN["tap_chi_y_duoc_thuc_hanh_175"]

SACH = """# THỰC TRẠNG XÉT NGHIỆM ALBUMIN NIỆU Ở NGƯỜI ĐÁI THÁO ĐƯỜNG

**ALBUMINURIA TESTING IN DIABETES**

Nguyễn Văn A¹*

## TÓM TẮT

**Giới thiệu chung:** Mô tả tỷ lệ xét nghiệm.

**Phương pháp:** Cắt ngang.

**Kết quả:** [CẦN SỐ]% được xét nghiệm.

**Kết luận:** Còn khoảng trống.

**Từ khoá:** đái tháo đường, albumin niệu, ngoại trú.

## ABSTRACT

**Background:** Testing rates.

**Keywords:** diabetes, albuminuria, outpatients.

## 1. ĐẶT VẤN ĐỀ

Bệnh thận mạn thường gặp [1],[2].

## 3. KẾT QUẢ

**Bảng 1. Đặc điểm**

| Đặc điểm | Giá trị |
|---|---|
| Tuổi | … |

Tỷ lệ là [CẦN SỐ]%.

## 4. BÀN LUẬN

So với y văn [2].

## 5. KẾT LUẬN

Cần cải thiện.

## TÀI LIỆU THAM KHẢO

[1] Tác giả A (2024). Bài 1. *Tạp chí*, 1, 1–2.

[2] Tác giả B (2025). Bài 2. *Tạp chí*, 2, 3–4.
"""


def _do(md: str):
    return KB.do_ban_thao(md, GH)


def test_ban_sach_khong_vi_pham():
    kq = _do(SACH)
    assert kq["vi_pham"] == [], kq["vi_pham"]
    assert kq["so_do"]["tltk"] == 2 and kq["so_do"]["bang"] == 1 and kq["so_do"]["o_can"] == 2


def test_tu_khoa_cham_phay_bi_bat():
    kq = _do(SACH.replace("đái tháo đường, albumin niệu, ngoại trú", "đái tháo đường; albumin niệu; ngoại trú"))
    assert any("chấm phẩy" in x and "TÓM TẮT" in x for x in kq["vi_pham"])


def test_qua_sau_tu_khoa():
    kq = _do(SACH.replace("đái tháo đường, albumin niệu, ngoại trú", "a, b, c, d, e, f, g"))
    assert any("7 từ khoá > 6" in x for x in kq["vi_pham"])


def test_nhan_ban_nhap_ai_va_loi_dan_he_bi_bat():
    md = SACH.replace("## TÓM TẮT", "> [BẢN NHÁP AI — TÁC GIẢ PHẢI VIẾT LẠI & CHỊU TRÁCH NHIỆM]\n\n## TÓM TẮT")
    md += "\n> Cần bác sĩ kiểm chứng.\n"
    loi = _do(md)["vi_pham"]
    assert any("bản nháp" in x for x in loi) and any("lời dặn của hệ" in x for x in loi)


def test_chu_trong_o_can_khong_tinh_dau_vet_may():
    """Ô [CẦN…] chờ điền có thể chứa chữ giống mã nội bộ («mã BTM») — không được báo K8 giả khi chưa có số liệu."""
    md = SACH.replace("Tỷ lệ là [CẦN SỐ]%.", "Tỷ lệ là [CẦN KẾT QUẢ THẬT: nhận định về việc ghi mã BTM tại khoa].")
    assert _do(md)["vi_pham"] == []


def test_qua_hai_muoi_tltk():
    ds = "\n\n".join(f"[{i}] Tác giả (2024). Bài {i}. *T*, 1, 1." for i in range(1, 22))
    md = SACH.split("## TÀI LIỆU THAM KHẢO")[0] + "## TÀI LIỆU THAM KHẢO\n\n" + ds + "\n"
    assert any("21 tài liệu tham khảo > 20" in x for x in _do(md)["vi_pham"])


def test_qua_nam_bang():
    them = "".join(f"\n**Bảng {i}. B**\n\n| A | B |\n|---|---|\n| 1 | 2 |\n" for i in range(2, 7))
    md = SACH.replace("Tỷ lệ là [CẦN SỐ]%.", "Tỷ lệ là [CẦN SỐ]%.\n" + them)
    assert any("6 bảng > 5" in x for x in _do(md)["vi_pham"])


def test_trich_dan_gop_mot_ngoac_bi_bat():
    assert any("Trích dẫn gộp" in x for x in _do(SACH.replace("[1],[2]", "[1, 2]"))["vi_pham"])


def test_trich_dan_o_ket_qua_va_ket_luan_bi_bat():
    loi = _do(SACH.replace("Tỷ lệ là [CẦN SỐ]%.", "Tỷ lệ là 40% [1].").replace("Cần cải thiện.",
                                                                              "Cần cải thiện [2]."))["vi_pham"]
    assert any("mục KẾT QUẢ" in x for x in loi) and any("mục KẾT LUẬN" in x for x in loi)


def test_tieu_de_qua_dai_va_chua_in_hoa():
    md = SACH.replace("# THỰC TRẠNG XÉT NGHIỆM ALBUMIN NIỆU Ở NGƯỜI ĐÁI THÁO ĐƯỜNG",
                      "# " + " ".join(["từ"] * 31))
    loi = _do(md)["vi_pham"]
    assert any("Tiêu đề 31 từ > 30" in x for x in loi) and any("chưa in hoa" in x for x in loi)


def test_tom_tat_qua_250_tu():
    md = SACH.replace("**Phương pháp:** Cắt ngang.", "**Phương pháp:** " + " ".join(["chữ"] * 260))
    assert any("TÓM TẮT" in x and "> 250" in x for x in _do(md)["vi_pham"])


def test_trang_chua_do_khong_bao_gio_la_dat(tmp_path, monkeypatch):
    """Không có Word (hoặc không xin đếm trang) ⇒ trang = None và có ghi chú «chưa đo»; ô [CẦN] + --nop ⇒ vi phạm."""
    p = tmp_path / "bt.md"
    p.write_text(SACH, encoding="utf-8", newline="\n")
    monkeypatch.setattr(KB, "dem_trang_word", lambda _d: None)
    kq = KB.kiem(p, TEN, docx=tmp_path / "x.docx", dem_trang=True)
    assert kq["so_do"]["trang"] is None and any("chưa đo" in x for x in kq["ghi_chu"]) and kq["ma"] == 0
    kq_nop = KB.kiem(p, TEN, nop=True)
    assert kq_nop["ma"] == 1 and any("ô [CẦN" in x for x in kq_nop["vi_pham"])


def test_qua_muoi_trang_theo_word_la_vi_pham(tmp_path, monkeypatch):
    p = tmp_path / "bt.md"
    p.write_text(SACH, encoding="utf-8", newline="\n")
    monkeypatch.setattr(KB, "dem_trang_word", lambda _d: {"trang": 15, "tu_word": 5173})
    kq = KB.kiem(p, TEN, docx=tmp_path / "x.docx", dem_trang=True)
    assert kq["ma"] == 1
    assert any("15 trang > 10" in x for x in kq["vi_pham"]) and any("5173 từ > 5000" in x for x in kq["vi_pham"])


def test_tap_chi_chua_khai_gioi_han_ma_2(tmp_path):
    p = tmp_path / "bt.md"
    p.write_text(SACH, encoding="utf-8", newline="\n")
    assert KB.kiem(p, "BMJ Open")["ma"] == 2
    assert KB.main([str(p), "--tap-chi", "Tạp chí không có"]) == 2


# ── Bảng gọn của hồ sơ tạp chí ─────────────────────────────────────────────────────────────────────────────────────
pytest.importorskip("docx", reason="python-docx chưa cài")


def _rong_cot(docx_path: Path):
    import re
    with zipfile.ZipFile(docx_path) as zf:
        xml = zf.read("word/document.xml").decode("utf-8")
    return [int(x) for x in re.findall(r'<w:tcW[^>]*w:w="(\d+)"', xml)], xml


_BANG = ("| Đặc điểm của đối tượng nghiên cứu dài | n | Tỷ lệ, % (KTC 95%) |\n|---|---|---|\n"
         "| Tuổi trung bình | … | … |\n")


def test_ho_so_ydth175_dung_bang_gon_cot_theo_noi_dung(tmp_path):
    out = tmp_path / "gon.docx"
    M2D.markdown_to_docx(_BANG, out, journal_profile=M2D.resolve_journal_profile(TEN))
    rong, xml = _rong_cot(out)
    hang_dau = rong[:3]
    assert hang_dau[0] > hang_dau[2] > hang_dau[1], hang_dau      # cột chữ rộng nhất, cột «n» hẹp nhất
    assert sum(hang_dau) == M2D.CONTENT_WIDTH_TWIPS
    assert 'w:jc w:val="both"' not in xml.split("<w:tbl>")[1].split("</w:tbl>")[0]  # ô dữ liệu căn trái, không dàn đều


def test_mac_dinh_khong_doi_bang_chia_deu(tmp_path):
    out = tmp_path / "deu.docx"
    M2D.markdown_to_docx(_BANG, out)
    rong, _ = _rong_cot(out)
    assert len(set(rong[:3])) == 1


def test_do_rong_cot_kep_trong_so():
    rows = [["x" * 200, "n", "y"], ["a", "b", "c"]]
    rong = M2D.do_rong_cot_theo_noi_dung(rows, 3, 9000)
    assert sum(rong) == 9000 and rong[1] == rong[2] and rong[0] < 9000 * 45 // 69 + 10
