"""Hồi quy 24/09/2026 — lệnh `tools/toan_van_guideline.py` nối 4 connector toàn văn guideline «mồ côi».

Bảo vệ:
  1. cờ tắt ⇒ mã thoát 3 + thông điệp rõ, không traceback; trên Cloud (CLAUDE_CODE_REMOTE=true) thông điệp chỉ
     sang cài đặt môi trường Cloud, Mac/Windows giữ thông điệp ~/.ebm-secrets cũ;
  2. `trich_van_ban_tu_pdf` giữ mặc định 200.000 ký tự nhưng BÁO khi bị cắt, trích được TOÀN BỘ khi
     gioi_han_ky_tu=None, và cho mốc trang để định vị;
  3. --tim tìm trong TOÀN BỘ tài liệu (không chỉ 200.000 ký tự đầu), trả vị trí + số trang;
  4. không tải NICE, không tải domain ngoài nguồn đã khảo sát, không lưu toàn văn vào repo — đều không gọi mạng;
  5. tải thất bại + có DOI/PMID ⇒ gợi ý đường lùi guideline_citation_summary.
Ngoại tuyến: PDF dựng bằng pypdf (nội dung tự chế), HttpClient giả. Không bật cờ trong app/config.py.
"""
from __future__ import annotations

import io
import json

import pytest

from app.config import settings
from app.sources import guideline_fulltext_common as common
from app.sources.guideline_fulltext_common import (
    GIOI_HAN_KY_TU_MAC_DINH,
    ConnectorChuaBat,
    KetQuaToanVanGuideline,
    thong_diep_co_tat,
    trang_cua_vi_tri,
    trich_van_ban_tu_pdf,
)
from tools import toan_van_guideline as T

CO = {
    "gold": "enable_gold_copd_fulltext",
    "gina": "enable_gina_asthma_fulltext",
    "bts": "enable_bts_guidelines_fulltext",
    "pmc": "enable_pmc_guideline_fulltext",
}


def _pdf(cac_trang: list[str]) -> bytes:
    """PDF nhiều trang có lớp văn bản — dựng bằng pypdf, nội dung tự chế (không bản quyền)."""
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    w = PdfWriter()
    font = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
    })
    font_ref = w._add_object(font)
    for chu in cac_trang:
        page = w.add_blank_page(width=600, height=200)
        s = DecodedStreamObject()
        s.set_data(f"BT /F1 10 Tf 5 100 Td ({chu}) Tj ET".encode("latin-1"))
        page[NameObject("/Contents")] = w._add_object(s)
        page[NameObject("/Resources")] = DictionaryObject({
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})})
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


@pytest.fixture(autouse=True)
def _tat_het_co(monkeypatch):
    for ten in CO.values():
        monkeypatch.setattr(settings, ten, False)
    monkeypatch.delenv("CLAUDE_CODE_REMOTE", raising=False)


# ── (c) Thông điệp cờ tắt theo môi trường ────────────────────────────────────

def test_thong_diep_co_tat_tren_cloud_chi_sang_cai_dat_moi_truong(monkeypatch):
    monkeypatch.setenv("CLAUDE_CODE_REMOTE", "true")
    tb = thong_diep_co_tat("gold_copd", "ENABLE_GOLD_COPD_FULLTEXT")
    assert "cài đặt môi trường Cloud" in tb and "PHIÊN MỚI" in tb
    assert "ENABLE_GOLD_COPD_FULLTEXT=true" in tb
    assert "đặt true trong" not in tb


def test_thong_diep_co_tat_tren_mac_giu_nguyen():
    tb = thong_diep_co_tat("gold_copd", "ENABLE_GOLD_COPD_FULLTEXT")
    assert tb == ("[gold_copd] ENABLE_GOLD_COPD_FULLTEXT chưa bật — đặt true trong "
                  "~/.ebm-secrets/medical-ebm-automation.env để dùng connector này.")


@pytest.mark.parametrize("nguon", ["gold", "gina", "bts", "pmc"])
def test_ca_bon_connector_raise_connector_chua_bat_voi_thong_diep_cloud(nguon, monkeypatch):
    monkeypatch.setenv("CLAUDE_CODE_REMOTE", "true")
    with pytest.raises(ConnectorChuaBat) as ei:
        T._dung_client(nguon)
    assert isinstance(ei.value, RuntimeError)  # tương thích nơi bắt RuntimeError cũ
    assert "cài đặt môi trường Cloud" in str(ei.value)


@pytest.mark.parametrize("argv", [["gold"], ["gina"], ["pmc", "PMC123"],
                                  ["bts", "https://www.brit-thoracic.org.uk/a.pdf"]])
def test_cli_co_tat_ma_thoat_3_khong_traceback(argv, capsys):
    assert T.main(argv) == T.MA_CHUA_BAT
    out = capsys.readouterr()
    assert "CONNECTOR CHƯA BẬT" in out.out
    assert "Traceback" not in out.out + out.err


# ── (b) Trích PDF: mặc định cũ, báo cắt, toàn bộ, mốc trang ─────────────────

def test_trich_pdf_mac_dinh_van_la_200000():
    assert GIOI_HAN_KY_TU_MAC_DINH == 200_000
    import inspect
    assert inspect.signature(trich_van_ban_tu_pdf).parameters["gioi_han_ky_tu"].default == 200_000


def test_trich_pdf_bao_cat_va_toan_bo_va_moc_trang():
    pdf = _pdf(["trang mot AAAA", "trang hai BBBB", "trang ba cum dich CCCC"])
    tt: dict = {}
    cat = trich_van_ban_tu_pdf(pdf, gioi_han_ky_tu=20, thong_tin=tt)
    assert len(cat) == 20 and tt["bi_cat"] is True and tt["so_trang_pdf"] == 3
    assert "cum dich" not in cat

    tt2: dict = {}
    du = trich_van_ban_tu_pdf(pdf, gioi_han_ky_tu=None, thong_tin=tt2)
    assert "cum dich" in du and tt2["bi_cat"] is False
    assert [so for so, _ in tt2["moc_trang"]] == [1, 2, 3]
    assert trang_cua_vi_tri(tt2["moc_trang"], du.index("cum dich")) == 3
    assert trang_cua_vi_tri(tt2["moc_trang"], 0) == 1

    tt3: dict = {}
    assert trich_van_ban_tu_pdf(pdf, thong_tin=tt3) == du  # ngắn hơn trần ⇒ không cắt
    assert tt3["bi_cat"] is False


# ── (a) Lệnh: tải, --tim toàn bộ, metadata ───────────────────────────────────

class _HttpGia:
    def __init__(self, pdf: bytes):
        self.pdf = pdf
        self.goi: list[str] = []

    def get_bytes(self, url, **kw):
        self.goi.append(url)
        return self.pdf

    def get_text(self, url, **kw):  # không được dùng khi đã có --url
        raise AssertionError("không được dò trang khi đã có URL")


def _bat_gold_voi_pdf(monkeypatch, pdf: bytes) -> _HttpGia:
    monkeypatch.setattr(settings, CO["gold"], True)
    http = _HttpGia(pdf)
    from app.sources import gold_copd
    goc_init = gold_copd.GoldCopdFullTextClient.__init__

    def init(self):
        goc_init(self)
        self.http = http

    monkeypatch.setattr(gold_copd.GoldCopdFullTextClient, "__init__", init)
    return http


def test_tim_trong_toan_bo_tai_lieu_khong_chi_200000_ky_tu(monkeypatch, capsys):
    # Trang 1 dài để đẩy cụm cần tìm ra SAU mốc cắt thử (gioi_han nhỏ qua monkeypatch mặc định).
    monkeypatch.setattr(T, "GIOI_HAN_KY_TU_MAC_DINH", 30)
    pdf = _pdf(["mo dau " + "x" * 60, "doan giua", "blood eosinophil count 300"])
    _bat_gold_voi_pdf(monkeypatch, pdf)
    url = "https://goldcopd.org/wp-content/uploads/2026/01/GOLD-REPORT-2026-v1.3-8Dec2025_WMV2.pdf"
    ma = T.main(["gold", "--url", url, "--tim", "blood   eosinophil", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert ma == T.MA_OK
    assert out["bi_cat"] is False and out["gioi_han_ky_tu"] is None
    tim = out["tim"][0]
    assert tim["so_khop"] == 1 and tim["doan"][0]["trang"] == 3
    assert out["nam_suy_tu_url"] == "2026" and out["phien_ban_suy_tu_url"] == "1.3"
    assert out["sha256_nguon"] == common.sha256_hex(pdf)
    assert out["so_trang_pdf"] == 3 and out["ngay_tai"]
    assert out["ghi_chu_ban_quyen"] == common.GHI_CHU_BAN_QUYEN_CHUAN
    assert "van_ban_trich" not in out  # không bao giờ in toàn văn


def test_khong_tim_thi_giu_mac_dinh_va_bao_bi_cat(monkeypatch, capsys):
    monkeypatch.setattr(T, "GIOI_HAN_KY_TU_MAC_DINH", 30)
    _bat_gold_voi_pdf(monkeypatch, _pdf(["mo dau " + "x" * 60, "trang hai"]))
    ma = T.main(["gold", "--url", "https://goldcopd.org/a.pdf"])
    txt = capsys.readouterr().out
    assert ma == T.MA_OK
    assert "ĐÃ BỊ CẮT" in txt and "Bản quyền:" in txt


def test_tim_khong_khop_ma_thoat_1(monkeypatch, capsys):
    _bat_gold_voi_pdf(monkeypatch, _pdf(["noi dung"]))
    assert T.main(["gold", "--url", "https://goldcopd.org/a.pdf", "--tim", "khong co"]) == T.MA_KHONG_KHOP


# ── (a) Ranh giới: NICE, domain lạ, lưu trong repo — không gọi mạng ──────────

@pytest.mark.parametrize("argv", [
    ["bts", "https://www.nice.org.uk/guidance/ng245/x.pdf"],
    ["gold", "--url", "https://www.nice.org.uk/x.pdf"],
    ["gold", "--url", "https://evil.example.com/GOLD-2026.pdf"],
    ["gina", "--url", "https://goldcopd.org/x.pdf"],
    ["gold", "--url", "http://goldcopd.org/x.pdf"],
])
def test_url_ngoai_nguon_bi_tu_choi_truoc_khi_goi_mang(argv, monkeypatch, capsys):
    for ten in CO.values():
        monkeypatch.setattr(settings, ten, True)
    monkeypatch.setattr(T, "tai", lambda *a, **k: pytest.fail("không được tải"))
    assert T.main(argv) == T.MA_TU_CHOI
    assert "TỪ CHỐI" in capsys.readouterr().out


def test_khong_luu_toan_van_vao_repo(monkeypatch, capsys):
    monkeypatch.setattr(T, "tai", lambda *a, **k: pytest.fail("không được tải"))
    assert T.main(["pmc", "PMC1", "--luu", str(T.REPO / "reports" / "x.txt")]) == T.MA_TU_CHOI


def test_luu_ngoai_repo_duoc(monkeypatch, tmp_path, capsys):
    _bat_gold_voi_pdf(monkeypatch, _pdf(["noi dung noi bo"]))
    dich = tmp_path / "gold.txt"
    assert T.main(["gold", "--url", "https://goldcopd.org/a.pdf", "--luu", str(dich)]) == T.MA_OK
    assert "noi dung noi bo" in dich.read_text(encoding="utf-8")


# ── Lỗi tải ⇒ nói rõ + gợi ý đường lùi ───────────────────────────────────────

def test_tai_that_bai_co_doi_goi_y_duong_lui(monkeypatch, capsys):
    monkeypatch.setattr(T, "tai", lambda *a, **k: KetQuaToanVanGuideline(
        to_chuc="BTS", url_nguon="https://www.brit-thoracic.org.uk/a.pdf", thanh_cong=False,
        ghi_chu="404 Client Error"))
    ma = T.main(["bts", "https://www.brit-thoracic.org.uk/a.pdf", "--doi", "10.1136/x"])
    txt = capsys.readouterr().out
    assert ma == T.MA_LOI
    assert "KHÔNG TẢI ĐƯỢC" in txt and "trich-dan --doi" in txt


def test_loi_ngoai_du_kien_khong_traceback(monkeypatch, capsys):
    def no(*a, **k):
        raise ConnectionError("proxy 403")

    monkeypatch.setattr(T, "tai", no)
    assert T.main(["pmc", "PMC1", "--pmid", "123"]) == T.MA_LOI
    txt = capsys.readouterr().out
    assert "proxy 403" in txt and "--pmid 123" in txt


def test_trich_dan_dung_duong_lui(monkeypatch, capsys):
    from app.sources import guideline_citation_summary as g
    monkeypatch.setattr(g, "lay_trich_dan_tom_tat", lambda doi=None, pmid=None: g.KetQuaTrichDanTomTat(
        thanh_cong=True, doi=doi, trich_dan="Tác giả. Tiêu đề. 2026.", tom_tat="tóm tắt", ghi_chu="abstract"))
    assert T.main(["trich-dan", "--doi", "10.1/x"]) == T.MA_OK
    assert "TÓM TẮT" in capsys.readouterr().out
    assert T.main(["trich-dan"]) == T.MA_TU_CHOI


def test_pmcid_sai_la_tu_choi(monkeypatch, capsys):
    monkeypatch.setattr(settings, CO["pmc"], True)
    assert T.main(["pmc", "khong-phai-pmcid"]) == T.MA_TU_CHOI
