"""Thí điểm 18/11/2026 — kiểm tổng quan tài liệu G0-T3/T4 bằng Claude API (`tools/kiem_tong_quan_g0_api.py`).

Bác sĩ chọn thí điểm hai khâu giá trị cao nhất (A12 + G0-T3/T4). Không gọi API/NCBI thật: khách giả tiêm vào; dưới
pytest mô-đun API tự từ chối dựng khách thật, đọc kho khoá thật hay ghi sổ chi phí thật.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parents[1]
for _d in (REPO, REPO / "tools"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import duyet_kiem_may_api as DK  # noqa: E402
import kiem_tong_quan_g0_api as K  # noqa: E402

S = "S1"
TH = {
    "schema": "g0/tong_hop_bang_chung/v1", "nguoi_soan": "tong-quan-y-van", "ngay_soan": "2026-11-01",
    "sang_loc": [
        {"pmid": "11111111", "thiet_ke_that": "Thử nghiệm ngẫu nhiên", "lien_quan": "truc_tiep",
         "tom_tat": "Tỷ lệ hài lòng 72,5% ở người bệnh ngoại trú."},
        {"pmid": "22222222", "thiet_ke_that": "Cắt ngang", "lien_quan": "khong", "tom_tat": "Bài về phẫu thuật.",
         "ly_do": "lạc đề"},
    ],
    "nguon_bo_sung": [{"doi": "10.1000/vn1", "tieu_de": "Khảo sát VN", "thiet_ke_that": "Cắt ngang",
                       "lien_quan": "truc_tiep", "tom_tat": "Hài lòng chung cao.", "cach_tim": "Crossref"}],
    "muc_bang_chung_sau_sang_loc": "Bằng chứng trực tiếp là khảo sát cắt ngang (PMID 11111111; doi:10.1000/vn1).",
    "tong_hop": "Thời gian chờ là lĩnh vực hài lòng thấp nhất (PMID 11111111).",
}
KT = {"schema": "g0/khoang_trong/v1", "phat_bieu_khoang_trong": "Chưa từng có nghiên cứu nào tại khoa C1a.",
      "loai_khoang_trong": ["boi_canh"], "muc_novelty": {"muc": "moi_hoan_toan", "y_nghia": "Mới hoàn toàn."}}
ABS = {
    "11111111": {"status": "resolved", "title": "Patient satisfaction in Vietnam: a cross-sectional survey",
                 "abstract": "We conducted a cross-sectional survey. Overall satisfaction was 72.5%. Waiting time "
                             "was the lowest-rated domain.", "publication_types": ["Journal Article"]},
    "22222222": {"status": "resolved", "title": "Outpatient satisfaction after surgery",
                 "abstract": "Satisfaction with outpatient care was assessed.",
                 "publication_types": ["Journal Article"]},
}
ABS_DOI = {"10.1000/vn1": {"status": "resolved", "title": "Survey in Vietnam",
                           "abstract": "Overall satisfaction was high in five hospitals.",
                           "publication_types": ["journal-article"], "nguon": "Crossref"}}


def _goc(tmp_path: Path, kt: bool = True) -> Path:
    out = tmp_path / "exports" / S
    out.mkdir(parents=True)
    (out / f"G0_TONG_HOP_BANG_CHUNG_{S}.json").write_text(json.dumps(TH, ensure_ascii=False), encoding="utf-8",
                                                          newline="\n")
    if kt:
        (out / f"G0_KHOANG_TRONG_{S}.json").write_text(json.dumps(KT, ensure_ascii=False), encoding="utf-8",
                                                       newline="\n")
    (out / "study_meta.json").write_text(json.dumps({"gate_params": {"G0": {
        "population": "Người bệnh ngoại trú tại khoa C1a", "primary_outcome": "Mức hài lòng chung"}}},
        ensure_ascii=False), encoding="utf-8", newline="\n")
    return tmp_path


def _resp(text):
    return SimpleNamespace(content=[SimpleNamespace(text=text)], stop_reason="end_turn", model="claude-sonnet-5-5",
                           usage=SimpleNamespace(input_tokens=100, output_tokens=20), stop_details=None)


def _he_thong(kw) -> str:
    s = kw.get("system")
    return s if isinstance(s, str) else "".join(b.get("text", "") for b in s or [])


class Khach:
    """Định tuyến theo lời dặn: phần A (G0-T3) · phần C (G0-T4) · còn lại là lời dặn A12 (phần B)."""

    def __init__(self, a=None, b=None, c=None):
        self.a, self.b, self.c, self.goi = a, b, c, []
        self.messages = self
        self.beta = SimpleNamespace(messages=self)

    def create(self, **kw):
        self.goi.append(kw)
        ht = _he_thong(kw)
        f = self.a if "nhiệm vụ G0-T3" in ht else (self.c if "nhiệm vụ G0-T4" in ht else self.b)
        return _resp(f(kw) if callable(f) else f)


def _a_dat(kw):
    nd = kw["messages"][0]["content"]
    ids = sorted(set(__import__("re").findall(r"\[(B\d{3})\]", nd)))
    o = {"muc": "", "trich": "", "ly_do": ""}
    return json.dumps({"ket_qua": [{"id": i, "thiet_ke": {**o, "muc": "dung"}, "lien_quan": {**o, "muc": "hop_ly"},
                                    "tom_tat": {**o, "muc": "trung_thuc"}} for i in ids]})


def _b_dat(kw):
    nd = kw["messages"][0]["content"]
    cau = json.loads(nd.split("CÂU KHẲNG ĐỊNH CẦN KIỂM:\n", 1)[1])
    return json.dumps({"ket_qua": [{"id": c["id"], "tham_chieu": [
        {"so": n, "muc": "khong_du_thong_tin", "trich": "", "ly_do": ""} for n in c["giao_tham_chieu"]]}
        for c in cau]})


C_RONG = json.dumps({"van_de": []})


def test_chay_kho_khong_goi_api(tmp_path, capsys):
    goc = _goc(tmp_path)
    kh = Khach(_a_dat, _b_dat, C_RONG)
    assert K.main(["--study", S], client=kh, goc=goc) == 0
    assert kh.goi == [] and "CHẠY KHÔ" in capsys.readouterr().out


def test_thieu_tep_tong_hop_thi_khong_kiem_duoc(tmp_path):
    (tmp_path / "exports" / S).mkdir(parents=True)
    assert K.main(["--study", S, "--goi-api"], client=Khach(), goc=tmp_path) == 2


def test_gop_chuoi_dinh_danh_lien_nhau_thanh_mot_nhom():
    van, so = K.doan_tong_hop({"tong_hop": "A (PMID 11111111; PMID 22222222). B doi:10.1000/x."})
    assert "[1, 2]" in van and "[3]" in van
    assert so == {"PMID 11111111": 1, "PMID 22222222": 2, "doi:10.1000/x": 3}


def test_moi_dat_thi_ma_0_va_bao_cao_mang_ma_bam(tmp_path):
    goc = _goc(tmp_path)
    kh = Khach(_a_dat, _b_dat, C_RONG)
    ma = K.main(["--study", S, "--goi-api"], client=kh, goc=goc, lay=lambda p: ABS, lay_doi=lambda d: ABS_DOI)
    js = json.loads((goc / "exports" / S / "kiem_may_api" / f"G0_KIEM_TONG_QUAN_{S}.json").read_text(encoding="utf-8"))
    assert ma == 0, js
    assert js["schema"] == "kiem_tong_quan_g0/v1" and js["tep"] == f"G0_TONG_HOP_BANG_CHUNG_{S}.json"
    assert len(js["tep_sha256"]) == 64 and f"G0_KHOANG_TRONG_{S}.json" in js["tep_phu"] and js["loi_dan_sha256"]
    assert {k["truong"] for k in js["a"]} == {"thiet_ke", "lien_quan", "tom_tat"} and len(js["a"]) == 9
    assert "Mức hài lòng chung" in js["pico"]


def test_phan_a_trich_nguyen_van_moi_giu_muc_sai(tmp_path):
    goc = _goc(tmp_path)

    def a(kw):
        d = json.loads(_a_dat(kw))
        for m in d["ket_qua"]:
            if m["id"] == "B001":
                m["thiet_ke"] = {"muc": "sai", "trich": "We conducted a cross-sectional survey",
                                 "ly_do": "là cắt ngang"}
                m["lien_quan"] = {"muc": "khong_hop_ly", "trich": "câu model tự bịa", "ly_do": "x"}
        return json.dumps(d)

    K.main(["--study", S, "--goi-api"], client=Khach(a, _b_dat, C_RONG), goc=goc, lay=lambda p: ABS,
           lay_doi=lambda d: ABS_DOI)
    js = json.loads((goc / "exports" / S / "kiem_may_api" / f"G0_KIEM_TONG_QUAN_{S}.json").read_text(encoding="utf-8"))
    a1 = {k["truong"]: k for k in js["a"] if k["id"] == "B001"}
    assert a1["thiet_ke"]["muc"] == "sai" and not a1["thiet_ke"]["co"]
    assert a1["lien_quan"]["muc"] == "can_xem" and "can_cu_khong_khop" in a1["lien_quan"]["co"]


def test_phan_a_so_trong_tom_tat_phai_co_trong_abstract(tmp_path):
    goc = _goc(tmp_path)
    th = dict(TH)
    th["sang_loc"] = [dict(TH["sang_loc"][0], tom_tat="Tỷ lệ hài lòng 81,3%.")] + TH["sang_loc"][1:]
    (goc / "exports" / S / f"G0_TONG_HOP_BANG_CHUNG_{S}.json").write_text(json.dumps(th, ensure_ascii=False),
                                                                           encoding="utf-8", newline="\n")
    ma = K.main(["--study", S, "--goi-api"], client=Khach(_a_dat, _b_dat, C_RONG), goc=goc, lay=lambda p: ABS,
                lay_doi=lambda d: ABS_DOI)
    js = json.loads((goc / "exports" / S / "kiem_may_api" / f"G0_KIEM_TONG_QUAN_{S}.json").read_text(encoding="utf-8"))
    tt = next(k for k in js["a"] if k["id"] == "B001" and k["truong"] == "tom_tat")
    assert tt["muc"] == "trung_thuc" and tt["co"] == ["so_khong_thay:81.3"] and ma == 1


def test_phan_c_dinh_danh_ngoai_danh_sach_va_trich_phat_bieu(tmp_path):
    goc = _goc(tmp_path)
    c = json.dumps({"van_de": [
        {"loai": "da_tra_loi", "dinh_danh": "PMID 99999999", "trich": "x", "ly_do": "bài không được giao"},
        {"loai": "tuyet_doi_hoa", "dinh_danh": "", "trich": "Chưa từng có nghiên cứu nào", "ly_do": "tuyệt đối"},
        {"loai": "novelty_khong_khop", "dinh_danh": "PMID 11111111", "trich": "Overall satisfaction was 72.5%",
         "ly_do": "đã có khảo sát"},
        {"loai": "loai_khong_khop", "dinh_danh": "", "trich": "câu model tự viết, không có trong phát biểu",
         "ly_do": "x"},
        {"loai": "bia_ra", "dinh_danh": "", "trich": "", "ly_do": ""}]})
    ma = K.main(["--study", S, "--goi-api"], client=Khach(_a_dat, _b_dat, c), goc=goc, lay=lambda p: ABS,
                lay_doi=lambda d: ABS_DOI)
    js = json.loads((goc / "exports" / S / "kiem_may_api" / f"G0_KIEM_TONG_QUAN_{S}.json").read_text(encoding="utf-8"))
    kc = {k["loai"]: k for k in js["c"]}
    assert kc["da_tra_loi"]["muc"] == "can_xem" and "dinh_danh_khong_duoc_giao" in kc["da_tra_loi"]["co"]
    assert kc["tuyet_doi_hoa"]["muc"] == "van_de" and not kc["tuyet_doi_hoa"]["co"]
    assert kc["novelty_khong_khop"]["muc"] == "van_de"
    assert kc["khong_kiem_duoc"]["muc"] == "khong_kiem_duoc"
    assert kc["loai_khong_khop"]["muc"] == "can_xem" and "can_cu_khong_khop" in kc["loai_khong_khop"]["co"]
    assert ma == 1


def test_phan_c_chi_giao_bai_truc_tiep_co_abstract_khong_giao_bai_lac_de(tmp_path):
    goc = _goc(tmp_path)
    kh = Khach(_a_dat, _b_dat, C_RONG)
    K.main(["--study", S, "--goi-api"], client=kh, goc=goc, lay=lambda p: ABS, lay_doi=lambda d: ABS_DOI)
    nd = next(g for g in kh.goi if "nhiệm vụ G0-T4" in _he_thong(g))["messages"][0]["content"]
    assert "PMID 11111111" in nd and "doi:10.1000/vn1" in nd and "PMID 22222222" not in nd


def test_lo_json_hong_hai_lan_thi_khong_kiem_duoc_khong_doan(tmp_path):
    goc = _goc(tmp_path)
    kh = Khach('{"ket_qua": [ {"id": "B001" "hỏng"', _b_dat, C_RONG)
    ma = K.main(["--study", S, "--goi-api"], client=kh, goc=goc, lay=lambda p: ABS, lay_doi=lambda d: ABS_DOI)
    js = json.loads((goc / "exports" / S / "kiem_may_api" / f"G0_KIEM_TONG_QUAN_{S}.json").read_text(encoding="utf-8"))
    assert all(k["muc"] == "khong_kiem_duoc" for k in js["a"])
    assert sum(1 for g in kh.goi if "nhiệm vụ G0-T3" in _he_thong(g)) == 2  # gửi đầu + đúng MỘT lần gửi lại
    assert ma in (0, 1, 2) and js["loi"]


def test_khong_abstract_nao_thi_ma_2(tmp_path):
    goc = _goc(tmp_path)
    ma = K.main(["--study", S, "--goi-api"], client=Khach(_a_dat, _b_dat, C_RONG), goc=goc,
                lay=lambda p: {}, lay_doi=lambda d: {})
    assert ma == 2


def test_duyet_kiem_may_liet_ke_muc_g0_va_bao_cao_cu_khi_khoang_trong_doi(tmp_path):
    goc = _goc(tmp_path)

    def a(kw):
        d = json.loads(_a_dat(kw))
        d["ket_qua"][0]["thiet_ke"] = {"muc": "sai", "trich": "We conducted a cross-sectional survey", "ly_do": "x"}
        return json.dumps(d)

    c = json.dumps({"van_de": [{"loai": "tuyet_doi_hoa", "dinh_danh": "", "trich": "Chưa từng có nghiên cứu nào",
                                "ly_do": "x"}]})
    K.main(["--study", S, "--goi-api"], client=Khach(a, _b_dat, c), goc=goc, lay=lambda p: ABS,
           lay_doi=lambda d: ABS_DOI)
    bcs = DK.doc_bao_cao(S, goc)
    khoa = {m["khoa"] for m in bcs["G0"]["muc"]}
    assert "G0A|PMID 11111111|thiet_ke" in khoa and any(k.startswith("G0C|tuyet_doi_hoa|") for k in khoa)
    assert DK.hieu_luc(bcs["G0"]["bc"], S, goc)[0] is False
    p = goc / "exports" / S / f"G0_KHOANG_TRONG_{S}.json"
    p.write_text(p.read_text(encoding="utf-8").replace("Chưa từng", "Chưa thấy"), encoding="utf-8", newline="\n")
    cu, ly_do = DK.hieu_luc(bcs["G0"]["bc"], S, goc)
    assert cu is True and "G0_KHOANG_TRONG" in ly_do


@pytest.mark.parametrize("bai,ket", [({"pmid": "123"}, 0), ({"pmid": "12345678"}, 1), ({"doi": "10.1/x"}, 1),
                                     ({"doi": "abc"}, 0)])
def test_bai_cua_g0_chi_nhan_dinh_danh_hop_le(bai, ket):
    assert len(K.bai_cua_g0({"sang_loc": [bai]})) == ket


# ── 18/11/2026 (thí điểm A12 trên C1a): «1.298 người bệnh» = dấu chấm phân cách NGHÌN kiểu Việt ──
@pytest.mark.parametrize("so,van,ky", [("1.298", "a sample of 1298 outpatients", True),
                                       ("4.372", "n = 4,372 patients", True), ("1.298", "1 298 người", True),
                                       ("1.298", "value 1.2985", False), ("0.02", "median 0.010", False),
                                       ("24.9", "24,9% had UACR", True)])
def test_so_co_trong_hieu_dau_cham_phan_cach_nghin(so, van, ky):
    import kiem_noi_dung_trich_dan as KND  # noqa: PLC0415

    assert KND.so_co_trong(so, van) is ky


def test_loi_dan_may_cham_dung_thang_lien_quan_bac_si_chot_tu_mot_nguon():
    """18/11/2026: bác sĩ chốt thang mức liên quan (khác nước vẫn trực tiếp; kết cục gần/quần thể con = gián tiếp; cùng
    quần thể khác khái niệm = không). Máy chấm phải dùng ĐÚNG văn bản thang của g0_tong_hop — không định nghĩa riêng."""
    import g0_tong_hop as GTH  # noqa: PLC0415

    assert GTH.thang_lien_quan() in K.HE_THONG_A
    assert set(GTH.DINH_NGHIA_LIEN_QUAN) == set(GTH.LIEN_QUAN)
    assert "KHÁC NƯỚC" in GTH.DINH_NGHIA_LIEN_QUAN["truc_tiep"]
    assert "KỂ CẢ khi cùng quần thể" in GTH.DINH_NGHIA_LIEN_QUAN["khong"]
