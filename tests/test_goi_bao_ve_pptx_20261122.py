"""Gói bảo vệ đề cương: tệp trình chiếu .pptx thật và câu hỏi từ sổ quyết định của hội đồng nghiên cứu (bác sĩ
22/11/2026: «Những vấn đề còn lại … có nền hay chưa có nền hãy hoàn thiện, bổ sung và nâng cấp đạt chuẩn»).

Trước bản này `goi_bao_ve_hoi_dong.py` chỉ ra dàn slide .md/.docx (không trình chiếu được) và bộ câu hỏi không đọc sổ
`hoi_dong_khoa_hoc/QUYET_DINH_HOI_DONG_*.md`. Fixture tự soạn, ngoại tuyến, dùng lại đề cương mẫu của test 21/11.
"""
from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (REPO_ROOT, REPO_ROOT / "tools"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import goi_bao_ve_hoi_dong as G  # noqa: E402

pptx = pytest.importorskip("pptx")
_spec = importlib.util.spec_from_file_location("t_goi_21", REPO_ROOT / "tests" / "test_goi_bao_ve_hoi_dong_20261121.py")
T0 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T0)
MA, DC = T0.MA, T0.DC

CHUONG_HINH = """# 5. DỰ KIẾN KẾT QUẢ

Kết quả trình bày theo từng mục tiêu.

![Hình 5.1](bieu-bang/hinh-5-1.png)

**Hình 5.1. Sơ đồ tuyển chọn đối tượng nghiên cứu (theo STROBE)**

*Ghi chú:* Số lượng ở từng bước được ghi khi kết thúc thu thập.

![Biểu đồ 5.1](bieu-bang/bieu-do-5-1.png)

**Biểu đồ 5.1. Tỷ lệ hài lòng theo lĩnh vực kèm KTC 95% (Mục tiêu 1)**

![Biểu đồ 5.2](bieu-bang/bieu-do-5-2.png)

**Biểu đồ 5.2. Hình chưa có tệp (Mục tiêu 2)**
"""
DE_CUONG = T0.DE_CUONG.replace("# 5. DỰ KIẾN KẾT QUẢ\n\nKết quả trình bày theo từng mục tiêu.\n", CHUONG_HINH)
CAU_MOI = "Chọn mẫu hệ thống phân tầng. Điểm bắt đầu được chọn ngẫu nhiên."
SO_QD = f"""# Sổ quyết định của hội đồng nghiên cứu — {MA}

- Ngày: 22/11/2026

## Thành viên: `thu.json`

### F01 — Cách chọn người bệnh chưa rõ điểm bắt đầu

- Quyết định: Ghi rõ điểm bắt đầu chọn ngẫu nhiên.
- Căn cứ: STROBE mục 6a.
- Căn cứ: Đề cương mục 4.4.2.
- Thay ở `{DC}` dòng 101
  - Cũ: Chọn mẫu hệ thống phân tầng.
  - Mới: {CAU_MOI}
- Thay ở `G4_A5_SAP_FINAL_{MA}.md` dòng 9
  - Cũ: a
  - Mới: b

### F02 — Mục kinh phí thiếu nguồn

- Quyết định: Bổ sung nguồn kinh phí.
- Căn cứ: Hướng dẫn chung mục 6.
- Thay ở `{DC}` dòng 140
  - Cũ: Kinh phí.

## 9.9. Đề mục chép trong khối cũ
  - Mới: Câu kinh phí đã bị sửa lại sau đó
    và còn một dòng tiếp.
- gạch đầu dòng chép trong khối mới
- Căn cứ: Căn cứ sau khối thay vẫn được nhận.

## Tài liệu đưa vào gói ký

- Không phát sinh tài liệu ký mới.
"""


def _png(p: Path, rong: int = 1200, cao: int = 800) -> None:
    from PIL import Image  # noqa: PLC0415

    p.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (rong, cao), (255, 255, 255)).save(p)


@pytest.fixture()
def goc(tmp_path: Path) -> Path:
    g = T0._dung(tmp_path / "exports", de_cuong=DE_CUONG)
    d = g / MA
    _png(d / "bieu-bang" / "hinh-5-1.png", 900, 1200)
    _png(d / "bieu-bang" / "bieu-do-5-1.png")
    (d / G.THU_MUC_HDKH).mkdir()
    (d / G.THU_MUC_HDKH / "QUYET_DINH_HOI_DONG_THU_20261122.md").write_text(SO_QD, encoding="utf-8", newline="\n")
    return g


def _trang(goc: Path):
    goi = G.dung_goi(MA, goc / MA)
    return G.dung_trang_pptx(goi["slides"], goi["ten_de_tai"], goi["dong"], goc / MA, goi["ten_dc"]), goi


# ── 1. Câu hỏi nhóm D từ sổ quyết định ──────────────────────────────────────────────────────────────────────────────
def test_so_quyet_dinh_thanh_cau_hoi_nhom_d(goc: Path) -> None:
    goi = G.dung_goi(MA, goc / MA)
    md = goi["cau_hoi_md"]
    assert "## D. Từ sổ quyết định của hội đồng nghiên cứu" in md
    assert "#### Câu D1 — F01 — sổ QUYET_DINH_HOI_DONG_THU_20261122.md" in md
    assert "- Hội đồng có thể chất vấn: «Cách chọn người bệnh chưa rõ điểm bắt đầu»" in md
    assert "- Quyết định của hội đồng nghiên cứu: «Ghi rõ điểm bắt đầu chọn ngẫu nhiên.»" in md
    assert "- Căn cứ: «STROBE mục 6a.»" in md and "- Căn cứ: «Đề cương mục 4.4.2.»" in md
    dong_cau = next(i for i, d in enumerate(DE_CUONG.splitlines(), 1) if CAU_MOI in d)
    assert f"- Đề cương hiện hành, dòng {dong_cau} (phần đã thay theo quyết định): «{CAU_MOI}»" in md
    assert f"không thuộc đề cương nộp: G4_A5_SAP_FINAL_{MA}.md." in md
    # phần «Mới» không còn nguyên văn ⇒ cảnh báo, không trình như đã thay
    d2 = md[md.index("Câu D2"):]
    assert "⚠ Phần đề cương thay theo quyết định (dòng gốc 140) không còn nguyên văn" in d2
    t = goi["tom_tat"]["cau_hoi"]
    assert t["D_so_quyet_dinh"] == 2 and t["D_canh_bao"] == 1 and t["D_tep"] == ["QUYET_DINH_HOI_DONG_THU_20261122.md"]
    assert "| Sổ quyết định hội đồng nghiên cứu | 1 sổ" in md


def test_doc_so_quyet_dinh_lay_mo_nhieu_dong(goc: Path) -> None:
    qd = G.doc_so_quyet_dinh(goc / MA / G.THU_MUC_HDKH / "QUYET_DINH_HOI_DONG_THU_20261122.md")
    assert [x["ma"] for x in qd] == ["F01", "F02"]
    # khối «Cũ»/«Mới» chép đề mục «## …» và dòng «- …» của đề cương: vẫn thuộc khối, không cắt sổ
    assert qd[1]["thay"][0]["moi"] == ["Câu kinh phí đã bị sửa lại sau đó", "và còn một dòng tiếp.",
                                       "- gạch đầu dòng chép trong khối mới"]
    assert qd[1]["can_cu"] == ["Hướng dẫn chung mục 6.", "Căn cứ sau khối thay vẫn được nhận."]
    assert qd[0]["can_cu"] == ["STROBE mục 6a.", "Đề cương mục 4.4.2."]


def test_khong_co_so_thi_khong_co_nhom_d(tmp_path: Path) -> None:
    g = T0._dung(tmp_path / "exports")
    md = G.dung_goi(MA, g / MA)["cau_hoi_md"]
    assert "## D." not in md


# ── 2. Tệp trình chiếu ───────────────────────────────────────────────────────────────────────────────────────────
def test_pptx_ghi_va_kiem_dat(goc: Path, tmp_path: Path) -> None:
    ra = tmp_path / "ra"
    assert G.main(["--study", MA, "--exports-root", str(goc), "--ghi", "--khong-word", "--thu-muc-ra", str(ra)]) == 0
    p = ra / G.TEN_PPTX.format(study=MA)
    (trang, canh_bao), goi = _trang(goc)
    assert G.kiem_pptx(p, trang, goi["dong"]) == []
    prs = pptx.Presentation(str(p))
    assert len(prs.slides) == len(trang) and len(trang) >= len(goi["slides"]) + 2
    assert any("Biểu đồ 5.2" in x and "không thấy tệp" in x for x in canh_bao)
    # hình đứng ngay sau slide liên quan: sơ đồ chọn sau «Phương pháp chọn mẫu», biểu đồ sau «Dự kiến kết quả»
    td = [t.tieu_de for t in trang]
    i_chon = max(i for i, x in enumerate(td) if "Phương pháp chọn mẫu" in x)
    assert td[i_chon + 1].startswith("Hình 5.1. Sơ đồ tuyển chọn")
    i_dk = max(i for i, x in enumerate(td) if "Dự kiến kết quả và phổ biến" in x)
    assert td[i_dk + 1].startswith("Biểu đồ 5.1.")
    # ảnh nhúng trùng từng byte tệp hình của đề cương
    anh = [sh for s in prs.slides for sh in s.shapes if sh.shape_type == 13]
    goc_anh = {hashlib.sha256((goc / MA / "bieu-bang" / x).read_bytes()).hexdigest()
               for x in ("hinh-5-1.png", "bieu-do-5-1.png")}
    assert {hashlib.sha256(a.image.blob).hexdigest() for a in anh} == goc_anh
    # mỗi trang trỏ mục đề cương: chân trang + ghi chú người trình bày
    s_chon = prs.slides[i_chon]
    assert "mục 4.4.2" in next(sh for sh in s_chon.shapes if sh.name == "ChanTrang").text_frame.text
    assert "mục 4.4.2 «Phương pháp chọn mẫu»" in s_chon.notes_slide.notes_text_frame.text
    assert "Ghi chú của hình (nguyên văn): Số lượng ở từng bước được ghi khi kết thúc thu thập." in \
        prs.slides[i_chon + 1].notes_slide.notes_text_frame.text


def test_bang_nguon_thanh_bang_that(goc: Path) -> None:
    (trang, _cb), _goi = _trang(goc)
    t = next(x for x in trang if "Sai số và hạn chế" in x.tieu_de)
    bang = next(k for k in t.khoi if k[0] == "bang")
    assert bang[1][0] == ("Nguồn sai lệch", "Biện pháp khống chế")
    assert bang[1][1][0] == ("Sai lệch chọn mẫu", "Chọn mẫu hệ thống có điểm bắt đầu ngẫu nhiên")


def test_kiem_pptx_bat_loi(goc: Path, tmp_path: Path) -> None:
    (trang, _cb), goi = _trang(goc)
    p = G.ghi_pptx(trang, tmp_path / "x.pptx")
    assert G.kiem_pptx(p, trang, goi["dong"]) == []
    prs = pptx.Presentation(str(p))
    i = next(k for k, t in enumerate(trang) if t.loai == "noi_dung" and any(
        g for kk in t.khoi if kk[0] == "chu" for _v, _d, g in kk[1]))
    than = next(sh for sh in prs.slides[i].shapes if sh.name == "Than")
    doan = next(pp for pp in than.text_frame.paragraphs if pp._p.pPr is not None and pp._p.pPr.get("marL"))
    doan.runs[0].text = "Câu máy tự viết không có trong đề cương."
    than.height = int(than.height * 0.3)
    prs.slides[i].notes_slide.notes_text_frame.text = "trống"
    prs.save(str(tmp_path / "y.pptx"))
    loi = G.kiem_pptx(tmp_path / "y.pptx", trang, goi["dong"])
    assert any("không nguyên văn đề cương" in x for x in loi)
    assert any("tràn chữ" in x for x in loi)
    assert any("thiếu nguồn" in x for x in loi)
    # ảnh nhúng khác tệp nguồn ⇒ lỗi
    j = next(k for k, t in enumerate(trang) if t.loai == "hinh")
    _png(tmp_path / "khac.png", 300, 300)
    trang[j].hinh = {**trang[j].hinh, "tep": tmp_path / "khac.png"}
    assert any("ảnh nhúng không trùng" in x for x in G.kiem_pptx(p, trang, goi["dong"]))


def test_chia_trang_khong_cat_cau_va_chu_toi_thieu(goc: Path) -> None:
    dai = " ".join(f"Câu dài số {k} nói về nội dung của mục phân tích số liệu với nhiều chữ để chiếm chỗ trên trang."
                   for k in range(40))
    sl = G.Slide(1, "phan_tich", "Xử lý và phân tích số liệu", 1.0,
                 khoi=[(None, [G.Cau(c, 10 + k) for k, c in enumerate(G.tach_cau(dai))])], nguon=["mục 4.10 «X»"])
    trang, _cb = G.dung_trang_pptx([sl], "Tên", ["x"] * 20, goc / MA, DC)
    assert len(trang) >= 2 and trang[1].tieu_de.endswith("(tiếp)")
    assert all(t.co == G.CO_THAN_TRANG >= 18 for t in trang)
    cau = [v for t in trang for k in t.khoi for v, _d, _g in k[1]]
    assert cau == G.tach_cau(dai)  # mỗi câu đúng một lần, nguyên văn, đúng thứ tự


def test_do_so_dong_bang_phong_that() -> None:
    ngan, dai = "Một câu ngắn.", "Một câu dài hơn nhiều " * 20
    assert G.so_dong_chu(ngan, 20, False, 10) == 1
    assert G.so_dong_chu(dai, 20, False, 10) > 1
    assert G.so_dong_chu(dai, 20, False, 5) > G.so_dong_chu(dai, 20, False, 10)
    assert G.so_dong_chu(dai, 24, False, 10) >= G.so_dong_chu(dai, 18, False, 10)


def test_neo_hinh() -> None:
    assert G._neo_hinh("Sơ đồ tuyển chọn đối tượng nghiên cứu (theo STROBE)") == "chon_mau"
    assert G._neo_hinh("Khung lý thuyết của nghiên cứu") == "khoang_trong"
    assert G._neo_hinh("Sơ đồ nhân quả (DAG) lựa chọn biến") == "phan_tich"
    assert G._neo_hinh("Tỷ lệ hài lòng (Mục tiêu 1)") == "du_kien"


def test_anh_xen_le_trang_hien_thi_nhung_tep_nhung_nguyen_ven(goc: Path, tmp_path: Path) -> None:
    """Sơ đồ matplotlib để trống nhiều lề trắng ⇒ trên slide XÉN hiển thị cho to rõ; tệp nhúng vẫn trùng từng byte."""
    from PIL import Image, ImageDraw  # noqa: PLC0415

    p = goc / MA / "bieu-bang" / "hinh-5-1.png"
    im = Image.new("RGB", (900, 1200), (255, 255, 255))
    ImageDraw.Draw(im).rectangle((300, 400, 600, 800), outline=(0, 0, 0), width=4)
    im.save(p)
    (trang, _cb), goi = _trang(goc)
    out = G.ghi_pptx(trang, tmp_path / "x.pptx")
    assert G.kiem_pptx(out, trang, goi["dong"]) == []
    prs = pptx.Presentation(str(out))
    i = next(k for k, t in enumerate(trang) if t.loai == "hinh" and t.hinh["rel"].endswith("hinh-5-1.png"))
    pic = next(sh for sh in prs.slides[i].shapes if sh.shape_type == 13)
    assert pic.crop_left > 0.2 and pic.crop_top > 0.2 and pic.crop_right > 0.2 and pic.crop_bottom > 0.2
    assert hashlib.sha256(pic.image.blob).hexdigest() == hashlib.sha256(p.read_bytes()).hexdigest()


def test_ngat_tu_khong_cat_giua_tu() -> None:
    """Ngắt theo TỪ như PowerPoint: ba từ, mỗi từ chiếm 0,6 bề rộng ⇒ ba dòng (ngắt theo ký tự chỉ ra hai dòng)."""
    tu = "Nghiêngnghiêng"
    rong_in = G._rong_pt(tu, 20, False) / 0.6 / 72.0
    assert G.so_dong_chu(" ".join([tu] * 3), 20, False, rong_in) == 3


# ── 23/11/2026: hàng bảng thấp hơn chiều cao đo 1 EMU (CI Linux) ──────────────────────────────────────────────────
@pytest.mark.parametrize("inch", [0.92, 0.1, 0.05, 1.234567, 3.3, 7.5])
def test_emu_tron_len_khong_thap_hon_chieu_cao_do(inch: float) -> None:
    """0,92 inch tính ra 841 247,9999… EMU; `Inches` cắt còn 841 247 ⇒ hàng thấp hơn chữ 1 EMU (> dung sai kiểm)."""
    e = G._emu_tron_len(inch)
    assert e / 914400.0 >= inch - 1e-9 and e - inch * 914400 < 1.0


def test_pptx_kiem_dat_voi_phong_mac_dinh_linux(goc: Path, tmp_path: Path, monkeypatch) -> None:
    """Máy không có Times New Roman (CI Ubuntu) dùng phông có chân mặc định của matplotlib (DejaVu Serif) — bộ dựng và
    bộ kiểm cùng phông nên tệp vẫn phải đạt. Trước bản vá: «trang 12: hàng bảng 2 tràn chữ»."""
    from matplotlib import font_manager as fm

    monkeypatch.setattr(G, "_duong_phong", lambda dam: fm.findfont(fm.FontProperties(
        family="DejaVu Serif", weight="bold" if dam else "normal"), fallback_to_default=True))
    monkeypatch.setattr(G, "_PHONG", {})
    ra = tmp_path / "ra"
    assert G.main(["--study", MA, "--exports-root", str(goc), "--ghi", "--khong-word", "--thu-muc-ra", str(ra)]) == 0
    (trang, _cb), goi = _trang(goc)
    assert G.kiem_pptx(ra / G.TEN_PPTX.format(study=MA), trang, goi["dong"]) == []
