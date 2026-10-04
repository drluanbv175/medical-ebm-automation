"""G10 nối hợp đồng ô trống chung (03–04/10/2026).

Đo 03/10: (1) nhánh «<…fill…>» quét XML THÔ của .docx nên khớp thẻ «<w:shd w:fill="D9EAF7"/>» md2docx_vn chèn cho hàng
tiêu đề MỌI bảng ⇒ G10-AUTO-09 báo nhầm VĨNH VIỄN, còn chữ thật «<điền tên>» (đã escape) lại không bao giờ khớp;
(2) `_real_text` của 6 mã tham chiếu readiness nhận «___», «[DỰ THẢO]», «[TO BE COMPLETED]», «?»… là mã thật;
(3) «[CAN» không ranh giới báo nhầm «[can thiệp]»/«[Cancer…]». Khoá: marker cũ vẫn bắt («[CAN_BO_SUNG]», «<Name>»,
«<date>»), báo nhầm được gỡ, ô mẫu khuôn sinh không lọt.
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import g10_quality_gate as G10Q  # noqa: E402


# ── _real_text (mã tham chiếu readiness) ──────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("v", ["___", "……", "[XÁC NHẬN THỦ CÔNG NGOÀI HỆ THỐNG]", "[DỰ THẢO]", "[TO BE COMPLETED]",
                               "[đơn vị]", "?", "-", "none", "N/A", "chưa quyết định", "[CẦN số IRB]", "<điền mã>",
                               "TO BE COMPLETED"])
def test_real_text_tu_choi(v):
    assert G10Q._real_text(v) is False, v


@pytest.mark.parametrize("v", ["IRB-2026-001", "G9-PI-REF-07", "[can thiệp] hướng dẫn", "Bệnh viện Quân y 175"])
def test_real_text_chap_nhan(v):
    assert G10Q._real_text(v) is True, v


# ── văn bản hiển thị ──────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("vb", ["Liên hệ: <điền tên>", "Chữ ký <Name>", "Ngày <date>", "Mục [CAN_BO_SUNG]",
                                "Kết cục [TODO]", "tại [nơi thực hiện]", "Institution: [TO BE COMPLETED]",
                                "| Số RCT | ? |", "Mã thiết kế nội bộ: None", "Kết quả `None`"])
def test_placeholder_hits_bat(vb):
    assert G10Q._placeholder_hits(vb), vb


@pytest.mark.parametrize("vb", ["[can thiệp] cộng đồng", "[Cancer cohort] người lớn", "tuổi < 18 hoặc > 80",
                                "Tỷ lệ là bao nhiêu ?", "Câu hỏi bao nhiêu ? Yếu tố nào liên quan",
                                "Trạng thái: [DỰ THẢO] — chờ PI"])
def test_placeholder_hits_khong_bao_nham(vb):
    assert G10Q._placeholder_hits(vb) == [], vb


def test_bang_kiem_soat_phien_ban_o_gia_tri_trong():
    vb = "| Phiên bản tài liệu | ___ |\n| Ngày tạo/cập nhật | 2026-10-04 |"
    hits = G10Q._placeholder_hits(vb)
    assert any("Phiên bản tài liệu" in h for h in hits) and not any("Ngày tạo" in h for h in hits)


def test_xml_sang_chu_bo_the_giai_ma_thuc_the():
    xml = ('<w:tbl><w:tr><w:tc><w:tcPr><w:shd w:fill="D9EAF7"/></w:tcPr><w:p><w:r><w:t>Tiêu đề</w:t></w:r></w:p></w:tc>'
           '</w:tr></w:tbl><w:p><w:r><w:t>Liên hệ: &lt;điền tên&gt;</w:t></w:r></w:p>')
    chu = G10Q._xml_sang_chu(xml)
    assert "w:fill" not in chu and "<điền tên>" in chu
    hits = G10Q._placeholder_hits(chu)
    assert len(hits) == 1 and "điền tên" in hits[0]


def test_docx_that_tu_md2docx_khong_bao_nham_bang(tmp_path):
    """Bản Word có bảng (md2docx_vn chèn w:shd w:fill cho hàng tiêu đề) và KHÔNG có ô trống ⇒ 0 khớp trên chữ hiển
    thị; bản quét XML thô cũ khớp thẻ shd."""
    pytest.importorskip("docx", reason="python-docx chưa cài trên máy/lane này")
    import md2docx_vn as MD
    md = tmp_path / "a.md"
    md.write_text("# Đề cương\n\n| Cột A | Cột B |\n|---|---|\n| 1 | 2 |\n\nNội dung đã điền.\n",
                  encoding="utf-8", newline="\n")
    out = MD.convert_markdown_file(md, tmp_path / "a.docx")
    with zipfile.ZipFile(out) as z:
        xml = z.read("word/document.xml").decode("utf-8")
        assert G10Q._PLACEHOLDER_RE.search(xml), "giả định của test: XML thô có thẻ khớp mẫu cũ (w:fill)"
        assert G10Q._placeholder_hits(G10Q._docx_visible_text(z, xml)) == []


def test_docx_that_con_o_trong_thi_bat(tmp_path):
    pytest.importorskip("docx", reason="python-docx chưa cài trên máy/lane này")
    import md2docx_vn as MD
    md = tmp_path / "b.md"
    md.write_text("# Đề cương\n\n| Mục | Giá trị |\n|---|---|\n| Địa điểm | [nơi thực hiện] |\n",
                  encoding="utf-8", newline="\n")
    out = MD.convert_markdown_file(md, tmp_path / "b.docx")
    with zipfile.ZipFile(out) as z:
        xml = z.read("word/document.xml").decode("utf-8")
        assert G10Q._placeholder_hits(G10Q._docx_visible_text(z, xml))
