"""Kiểm trích dẫn trên TOÀN VĂN cho các cặp A12 «cần xem» (21/11/2026, bác sĩ chọn C).

Đo thật: PMC XML chỉ phủ 3/13 tài liệu cần xem của C1a; thêm PDF đính kèm EndNote ⇒ 9/13 (BTM 12/12). Câu tiếng Việt
«0,78» phải khớp bài tiếng Anh «.78». Ngoại tuyến: XML/PDF/EndNote/khách API đều giả.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parents[1]
for _d in (REPO, REPO / "tools"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import kiem_trich_dan_toan_van as K  # noqa: E402

S = "S1"
VAN = (
    "# ĐỀ CƯƠNG\n# 4. PHƯƠNG PHÁP\n"
    "Câu đạt khi I-CVI ≥ 0,78, toàn thang đạt khi S-CVI/Ave ≥ 0,90 [1].\n"
    "Hệ số tương quan nội cụm thường dưới 0,05 [2].\n"
    "# 7. TÀI LIỆU THAM KHẢO\n"
    "1. Polit DF, Beck CT. Is the CVI an acceptable indicator of content validity? Res Nurs Health. 2007. "
    "doi:10.1002/nur.20199. PMID: 17654487.\n"
    "2. Adams G. Patterns of intra-cluster correlation. J Clin Epidemiol. 2004. doi:10.1016/j.jclinepi.2003.12.013. "
    "PMID: 15485730.\n"
)
DAI = ("Is the CVI an acceptable indicator of content validity? Appraisal and recommendations. Polit DF, Beck CT. "
       "Research in Nursing Health 2007. " + "Background text about questionnaires and nursing methods. " * 60)
POLIT = (DAI + "We recommend an I-CVI of .78 or higher and an S-CVI/Ave of .90 or higher for excellent content "
         "validity. " + "Other unrelated discussion of scaling. " * 40)


def _resp(text):
    return SimpleNamespace(content=[SimpleNamespace(text=text)], stop_reason="end_turn", model="claude-sonnet-5-5",
                           usage=SimpleNamespace(input_tokens=1000, output_tokens=100), stop_details=None)


class KhachGia:
    def __init__(self, tra):
        self.tra, self.goi = tra, []
        self.messages = self
        self.beta = SimpleNamespace(messages=self)

    def create(self, **kw):
        self.goi.append(kw)
        return _resp(self.tra(kw) if callable(self.tra) else self.tra)


def _goc(tmp_path: Path, cap=None, a12_cu=False) -> Path:
    d = tmp_path / "exports" / S
    (d / "kiem_may_api").mkdir(parents=True)
    (d / "toan_van_oa").mkdir()
    (d / f"DE_CUONG_NOP_HOI_DONG_{S}.md").write_text(VAN, encoding="utf-8", newline="\n")
    sha = hashlib.sha256((d / f"DE_CUONG_NOP_HOI_DONG_{S}.md").read_bytes()).hexdigest()
    cau = [{"id": "C001", "cau": "Câu đạt khi I-CVI ≥ 0,78, toàn thang đạt khi S-CVI/Ave ≥ 0,90 [1].", "so": [1]},
           {"id": "C002", "cau": "Hệ số tương quan nội cụm thường dưới 0,05 [2].", "so": [2]}]
    kq = cap if cap is not None else [
        {"id": "C001", "so": 1, "muc": "ho_tro_mot_phan", "ly_do": "abstract không nêu S-CVI/Ave",
         "trich": "content validity index", "co": []},
        {"id": "C002", "so": 2, "muc": "ho_tro", "ly_do": "", "trich": "", "co": []}]
    bc = {"tep": f"DE_CUONG_NOP_HOI_DONG_{S}.md", "tep_sha256": "0" * 64 if a12_cu else sha,
          "luc": "2026-11-21T08:00:00", "cau": cau, "ket_qua": kq}
    p = d / "kiem_may_api" / f"A12_KIEM_NOI_DUNG_{S}.json"
    p.write_text(json.dumps(bc, ensure_ascii=False), encoding="utf-8", newline="\n")
    return tmp_path


def _xml(goc: Path, pmid: str, than: str) -> None:
    x = (f'<article><front><article-meta><title-group><article-title>Tieu de</article-title></title-group>'
         f'</article-meta></front><body><sec><p>{than}</p></sec></body></article>')
    p = goc / "exports" / S / "toan_van_oa" / f"PMID-{pmid}_PMC1.xml"
    p.write_text(x, encoding="utf-8", newline="\n")


class EndNoteGia:
    """Thay `endnote_suc_khoe`: sdb trong bộ nhớ, PDF thật dưới <thư viện>.Data/PDF."""

    def __init__(self, tmp_path: Path, pmid_co_pdf=(), pmid_khong_pdf=(), pmid_thung_rac=()):
        self.tv = tmp_path / "Lib.enl"
        (tmp_path / "Lib.Data" / "PDF" / "1").mkdir(parents=True)
        self.kn = sqlite3.connect(":memory:")
        self.kn.executescript("CREATE TABLE refs (id INTEGER, accession_number TEXT, electronic_resource_number TEXT, "
                              "trash_state INTEGER); CREATE TABLE file_res (refs_id INTEGER, file_path TEXT);")
        for i, p in enumerate(pmid_co_pdf, 1):
            self.kn.execute("INSERT INTO refs VALUES (?, ?, '', 0)", (i, p))
            self.kn.execute("INSERT INTO file_res VALUES (?, ?)", (i, f"1/bai{i}.pdf"))
            (tmp_path / "Lib.Data" / "PDF" / "1" / f"bai{i}.pdf").write_bytes(b"%PDF-1.4 gia")
        for j, p in enumerate(pmid_khong_pdf, 100):
            self.kn.execute("INSERT INTO refs VALUES (?, ?, '', 0)", (j, p))
        for j, p in enumerate(pmid_thung_rac, 200):  # bản ghi trong thùng rác có PDF — không được dùng
            self.kn.execute("INSERT INTO refs VALUES (?, ?, '', 1)", (j, p))
            self.kn.execute("INSERT INTO file_res VALUES (?, ?)", (j, f"1/rac{j}.pdf"))
            (tmp_path / "Lib.Data" / "PDF" / "1" / f"rac{j}.pdf").write_bytes(b"%PDF-1.4 rac")

    @contextlib.contextmanager
    def ban_sao_csdl(self, thu_vien):
        yield self.kn

    def _chuan_doi(self, d):
        return d.lower()

    def thu_vien_cau_hinh(self):
        return self.tv


def test_so_chuan_hoa_hai_ngon_ngu_va_bo_so_trich_dan():
    assert K._so("I-CVI ≥ 0,78, S-CVI/Ave ≥ 0,90 [42]") == {".78", ".90"}
    assert K._so("I-CVI of .78 and .90") == {".78", ".90"}
    assert "38" not in K._so("theo hai nghiên cứu [38, 41] với 24,9%") and "24.9" in K._so("24,9% [3]")


def test_doan_lien_quan_lay_cua_so_co_so_lieu_ngoai_phan_dau():
    d = K.doan_lien_quan(POLIT, ["I-CVI ≥ 0,78, S-CVI/Ave ≥ 0,90 [1]"], "content validity", toi_da=4000)
    assert "I-CVI of .78" in d and len(d) <= 4000 + 10
    assert d.startswith(POLIT[:100])  # phần đầu (tiêu đề + abstract) luôn có


def test_pmc_xml_doc_than_bai():
    assert "S-CVI/Ave of .90" in K.van_pmc_xml(_luu_xml_tam(POLIT))


def _luu_xml_tam(than: str) -> Path:
    import tempfile
    p = Path(tempfile.mkdtemp()) / "a.xml"
    p.write_text(f"<article><body><p>{than}</p></body></article>", encoding="utf-8", newline="\n")
    return p


def test_thu_tu_nguon_xml_roi_pdf_tay_roi_endnote(tmp_path, monkeypatch):
    goc = _goc(tmp_path)
    ex = goc / "exports" / S
    tl1 = SimpleNamespace(pmid="17654487", doi="10.1002/nur.20199", van="Polit")
    es = EndNoteGia(tmp_path, pmid_co_pdf=["17654487"])
    monkeypatch.setattr(K, "van_pdf", lambda b: POLIT)
    assert K.tim_toan_van(1, tl1, ex, es.tv, es)[1].startswith("EndNote rec")
    (ex / "toan_van_tltk").mkdir()
    (ex / "toan_van_tltk" / "TLTK-1.pdf").write_bytes(b"%PDF tay")
    assert K.tim_toan_van(1, tl1, ex, es.tv, es)[1] == "PDF đặt tay TLTK-1.pdf"
    _xml(goc, "17654487", POLIT)
    assert K.tim_toan_van(1, tl1, ex, es.tv, es)[1].startswith("PMC XML")


def test_pdf_khong_co_lop_chu_va_ban_ghi_khong_tep(tmp_path, monkeypatch):
    goc = _goc(tmp_path)
    ex = goc / "exports" / S
    es = EndNoteGia(tmp_path, pmid_co_pdf=["17654487"], pmid_khong_pdf=["15485730"])
    monkeypatch.setattr(K, "van_pdf", lambda b: "ảnh")  # ít chữ ⇒ quét ảnh
    chu, ly = K.tim_toan_van(1, SimpleNamespace(pmid="17654487", doi="", van=""), ex, es.tv, es)
    assert chu == "" and "không có lớp chữ" in ly
    chu, ly = K.tim_toan_van(2, SimpleNamespace(pmid="15485730", doi="", van=""), ex, es.tv, es)
    assert chu == "" and "không có PDF đính kèm" in ly
    es2 = EndNoteGia(tmp_path / "r", pmid_thung_rac=["15485730"])
    monkeypatch.setattr(K, "van_pdf", lambda b: POLIT)
    chu, ly = K.tim_toan_van(2, SimpleNamespace(pmid="15485730", doi="", van=""), ex, es2.tv, es2)
    assert chu == "" and "không có bản ghi khớp" in ly
    chu, ly = K.tim_toan_van(2, SimpleNamespace(pmid="15485730", doi="", van=""), ex, None, None)
    assert chu == "" and "không đo được" in ly


def _tra(muc="ho_tro", trich="an S-CVI/Ave of .90 or higher"):
    return json.dumps({"ket_qua": [{"id": "C001", "so": 1, "muc": muc, "trich": trich, "ly_do": "có ở toàn văn"}]})


def test_trich_khong_nguyen_van_thi_khong_xac_minh():
    cap = [{"id": "C001", "so": 1, "muc": "ho_tro_mot_phan", "cau": "x", "ly_do": ""}]
    ra, _ = K.kiem_tai_lieu(1, cap, POLIT, "claude-sonnet-5-5", KhachGia(_tra(trich="cụm không hề có")))
    assert ra[0]["muc_toan_van"] == "khong_xac_minh" and ra[0]["trich"] == ""
    ra, _ = K.kiem_tai_lieu(1, cap, POLIT, "claude-sonnet-5-5", KhachGia(_tra(muc="dai_khai")))
    assert ra[0]["muc_toan_van"] == "khong_xac_minh"
    ra, _ = K.kiem_tai_lieu(1, cap, POLIT, "claude-sonnet-5-5", KhachGia(_tra()))
    assert ra[0]["muc_toan_van"] == "ho_tro" and ra[0]["muc_abstract"] == "ho_tro_mot_phan"


def test_chay_kho_khong_goi_api(tmp_path, monkeypatch, capsys):
    goc = _goc(tmp_path)
    _xml(goc, "17654487", POLIT)
    monkeypatch.setenv("EBM_WORKSPACE_ROOT", str(tmp_path / "khong-co"))
    assert K.main(["--study", S, "--json"], client=KhachGia(lambda kw: 1 / 0), goc=goc, es=None) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["so_cap"] == 1 and out["so_luot_goi"] == 1 and isinstance(out["uoc_usd"], float)
    assert not (goc / "exports" / S / "kiem_may_api" / f"A12_TOAN_VAN_{S}.json").exists()


def test_a12_cu_hoac_khong_co_toan_van_thi_khong_kiem_duoc(tmp_path, capsys):
    goc_a = _goc(tmp_path / "a", a12_cu=True)
    _xml(goc_a, "17654487", POLIT)  # có toàn văn — chỉ A12 cũ là lý do chặn
    kh = KhachGia(_tra())
    assert K.main(["--study", S, "--goi-api"], client=kh, goc=goc_a, es=None) == 2
    assert not kh.goi and "A12 không dùng được" in capsys.readouterr().out
    assert K.main(["--study", S, "--goi-api"], client=KhachGia(lambda kw: 1 / 0), goc=_goc(tmp_path / "b"),
                  es=None) == 2


def test_goi_api_ghi_bao_cao_va_ma_thoat(tmp_path):
    goc = _goc(tmp_path)
    _xml(goc, "17654487", POLIT)
    kh = KhachGia(_tra())
    assert K.main(["--study", S, "--goi-api"], client=kh, goc=goc, es=None) == 0
    assert len(kh.goi) == 1 and "ĐOẠN TRÍCH TỪ TOÀN VĂN CỦA TÀI LIỆU [1]" in kh.goi[0]["messages"][0]["content"]
    bc = json.loads((goc / "exports" / S / "kiem_may_api" / f"A12_TOAN_VAN_{S}.json").read_text(encoding="utf-8"))
    assert bc["so_ho_tro"] == 1 and bc["so_con_xem"] == 0 and bc["ket_qua"][0]["nguon"].startswith("PMC XML")
    md = (goc / "exports" / S / "kiem_may_api" / f"A12_TOAN_VAN_{S}.md").read_text(encoding="utf-8")
    assert "**ho_tro**" in md and "Cần bác sĩ kiểm chứng" in md
    assert K.main(["--study", S, "--goi-api"], client=KhachGia(_tra(muc="khong_ho_tro")), goc=goc, es=None) == 1


def test_vuot_tran_thi_khong_goi(tmp_path, monkeypatch):
    goc = _goc(tmp_path)
    _xml(goc, "17654487", POLIT)
    monkeypatch.setenv("EBM_API_CLAUDE_TRAN_USD_THANG", "0.00001")
    kh = KhachGia(_tra())
    assert K.main(["--study", S, "--goi-api"], client=kh, goc=goc, es=None) == 2
    assert not kh.goi
    assert not (goc / "exports" / S / "kiem_may_api" / f"A12_TOAN_VAN_{S}.json").exists()  # chặn trước, không ghi


@pytest.mark.parametrize("muc", ["khong_ho_tro", "ho_tro_mot_phan", "can_xem"])
def test_chi_lay_cap_can_xem(muc):
    bc = {"cau": [{"id": "C1", "cau": "x"}], "ket_qua": [{"id": "C1", "so": 1, "muc": muc}, {"id": "C1", "so": 2,
                                                                                         "muc": "ho_tro"}]}
    assert [c["so"] for c in K.cap_can_xem(bc)] == [1]


# ── 21/11/2026 lượt thật: chữ PDF tiếng Việt không ở dạng NFC; JSON hỏng; nghi PDF gắn nhầm bài ─────────────────────
def test_chu_pdf_dang_to_hop_van_khop_trich_nfc(tmp_path, monkeypatch):
    import unicodedata
    goc = _goc(tmp_path)
    ex = goc / "exports" / S
    nfd = unicodedata.normalize("NFD", DAI + " Sự hài lòng của người bệnh ngoại trú đạt 85,2%. " + "x " * 50)
    monkeypatch.setattr(K, "van_pdf", lambda b: nfd)
    (ex / "toan_van_tltk").mkdir()
    (ex / "toan_van_tltk" / "TLTK-1.pdf").write_bytes(b"%PDF tay")
    chu, _ng = K.tim_toan_van(1, SimpleNamespace(pmid="", doi="", van=VAN.splitlines()[-2]), ex, None, None)
    assert unicodedata.is_normalized("NFC", chu)
    cap = [{"id": "C001", "so": 1, "muc": "can_xem", "cau": "x", "ly_do": ""}]
    kh = KhachGia(_tra(trich="Sự hài lòng của người bệnh ngoại trú"))
    ra, _ = K.kiem_tai_lieu(1, cap, chu, "claude-sonnet-5-5", kh)
    assert ra[0]["muc_toan_van"] == "ho_tro"


def test_toan_van_khong_khop_tieu_de_thi_khong_dung(tmp_path, monkeypatch):
    goc = _goc(tmp_path)
    ex = goc / "exports" / S
    monkeypatch.setattr(K, "van_pdf", lambda b: "Completely different article about cardiology trials. " * 80)
    (ex / "toan_van_tltk").mkdir()
    (ex / "toan_van_tltk" / "TLTK-1.pdf").write_bytes(b"%PDF tay")
    chu, ly = K.tim_toan_van(1, SimpleNamespace(pmid="", doi="", van=VAN.splitlines()[-2]), ex, None, None)
    assert chu == "" and "nghi gắn nhầm bài" in ly


def test_json_hong_gui_lai_dung_mot_lan():
    cap = [{"id": "C001", "so": 1, "muc": "can_xem", "cau": "x", "ly_do": ""}]
    dem = {"n": 0}

    def tra(kw):
        dem["n"] += 1
        return '{"ket_qua": [{"id": "C001", "trich": "chuỗi hỏng' if dem["n"] == 1 else _tra()

    ra, _ = K.kiem_tai_lieu(1, cap, POLIT, "claude-sonnet-5-5", KhachGia(tra))
    assert dem["n"] == 2 and ra[0]["muc_toan_van"] == "ho_tro"
    with pytest.raises(K.API.KetQuaHong):
        K.kiem_tai_lieu(1, cap, POLIT, "claude-sonnet-5-5", KhachGia('{"ket_qua": [ hỏng'))


def test_loi_nhan_mang_dong_tltk_va_giu_trich_may():
    cap = [{"id": "C001", "so": 1, "muc": "can_xem", "cau": "x", "ly_do": ""}]
    kh = KhachGia(_tra(trich="không có trong đoạn"))
    ra, _ = K.kiem_tai_lieu(1, cap, POLIT, "claude-sonnet-5-5", kh, tltk="Polit DF. Is the CVI acceptable?")
    assert "TÀI LIỆU [1] TRONG DANH MỤC THAM KHẢO: Polit DF." in kh.goi[0]["messages"][0]["content"]
    assert ra[0]["muc_toan_van"] == "khong_xac_minh" and ra[0]["trich_may"] == "không có trong đoạn"


def test_pdf_cat_dong_giua_tu_van_khop_nhung_dien_dat_lai_thi_khong():
    doan = "ưa cao v\nới \nt\nỷ lệ 16,7 \n-\n \n69,2% b\nệnh nhân đ\nư\nợc k\nê đơn ít nh\nất 1 \nl\nần. Trong đó"
    assert K.co_nguyen_van_toan_van("tỷ lệ 16,7 - 69,2% bệnh nhân được kê đơn ít nhất 1 lần", doan)
    assert not K.co_nguyen_van_toan_van("tỷ lệ 16,7–69,2% người bệnh được kê đơn", doan)  # diễn đạt lại
    assert not K.co_nguyen_van_toan_van("1 lần", doan)  # quá ngắn để so bỏ khoảng trắng


def test_gach_noi_ngat_dong_van_khop():
    doan = ("Floor or ceiling effects are considered to be present if more than 15% of respondents achieved the lowest "
            "or high- est possible score, respectively [41].")
    assert K.co_nguyen_van_toan_van("more than 15% of respondents achieved the lowest or highest possible score",
                                    doan)
    # gạch nối thật («cross-cultural») ngắt dòng vẫn khớp nhờ phép so bỏ khoảng trắng
    assert K.co_nguyen_van_toan_van("cross-cultural validity", "and cross- cultural validity were")
