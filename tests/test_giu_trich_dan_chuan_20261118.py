"""Hồi quy 18/11/2026 — GIỮ trích dẫn đạt chuẩn khi chưa có toàn văn (bác sĩ: «Riêng với đề tài C1a hãy giữ lại trích
dẫn đủ tiêu chuẩn của nghiên cứu y khoa chuẩn»).

Luật toàn văn (G10-AUTO-12) chặn TLTK «không lấy được toàn văn». Bác sĩ cho riêng từng đề tài giữ những TLTK đạt chuẩn
trích dẫn: `GIU_TRICH_DAN_CHUAN_<mã>.json` (nguyên văn lời bác sĩ) + ba tiêu chí máy đo lại mỗi lần chạy (định danh ·
rút bài · loại nguồn). Bài giữ mà bị rút ⇒ mất quyền giữ (BLOCK); kiểm rút bài quá hạn ⇒ REVIEW.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

import toan_van_trich_dan as TVT  # noqa: E402

S = "SYNTH-GIU-CHUAN"
LOI = "Riêng với đề tài này hãy giữ lại trích dẫn đủ tiêu chuẩn của nghiên cứu y khoa chuẩn"
DE_CUONG = (
    "# ĐỀ CƯƠNG\n\nNền tảng [1–4].\n\n# 7. TÀI LIỆU THAM KHẢO\n\n"
    "1. Tác giả A. Phương pháp hiệu chỉnh tách biệt trong hồi quy. Tạp chí Thống kê. 2002. doi:10.1000/abc1. "
    "PMID: 11111111.\n"
    "2. Tác giả B. Bài hai có toàn văn. Tạp chí. 2021. PMID: 22222222.\n"
    "3. Bộ Y tế. Quyết định số 56/QĐ-BYT ngày 08/01/2024 ban hành hướng dẫn đo lường hài lòng. Hà Nội: Bộ Y tế; 2024.\n"
    "4. Tác giả D. Sự hài lòng của người bệnh ngoại trú tại bệnh viện tuyến cuối. Tạp chí Y học Cộng đồng. 2023. "
    "doi:10.1000/d4.\n"
    "5. Lwanga SK, Lemeshow S. Sample size determination in health studies. Geneva: World Health Organization; 1991.\n"
)
CROSSREF = {"10.1000/d4": {"title": ["Sự hài lòng của người bệnh ngoại trú tại bệnh viện tuyến cuối"],
                           "issued": {"date-parts": [[2023]]}, "type": "journal-article",
                           "container-title": ["Tạp chí Y học Cộng đồng"]}}


def _ghi(p: Path, van) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(van if isinstance(van, str) else json.dumps(van, ensure_ascii=False), encoding="utf-8", newline="\n")


def _luc(ngay_truoc: int = 0) -> str:
    return (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=ngay_truoc)).isoformat()


def _de_tai(tmp_path: Path, *, rut_pmid: str = "ok", tuoi_rut: int = 2, rut_doi: str = "ok",
            meta: bool = True) -> Path:
    d = tmp_path / S
    _ghi(d / f"DE_CUONG_NOP_HOI_DONG_{S}.md", DE_CUONG)
    bn = TVT.dung_bien_nhan(d, S, toan_van=False, nguon="endnote", nguoi_do="kiểm thử")
    hai_lan = [{"lan": "truy_cap_mo", "ngay": "2026-11-01", "ket_qua": "không có bản mở"},
               {"lan": "trinh_duyet", "ngay": "2026-11-02", "ket_qua": "không có quyền"}]
    for m in bn["muc"]:
        if "pmid:22222222" in m["khoa"]:
            m["toan_van"] = True
        elif m["so"] in (1, 3):
            m["lan_da_thu"] = hai_lan  # đã thử đủ hai làn ⇒ «không lấy được»
        # TLTK 4, 5: còn làn chưa thử
    TVT.ghi_bien_nhan(d, S, bn)
    if meta:
        _ghi(d / "A12_METADATA_RECEIPT.json", {"metadata": {"11111111": {
            "status": "resolved", "title": "Phương pháp hiệu chỉnh tách biệt trong hồi quy",
            "journal": "Tạp chí Thống kê", "year": "2002", "doi": "10.1000/abc1"}}})
    _ghi(d / "A12_RETRACTION_RECEIPT.json", {"checked_at_utc": _luc(tuoi_rut),
                                             "results": {"11111111": {"status": rut_pmid}}})
    _ghi(d / f"KIEM_RUT_BAI_TRICH_DAN_{S}.json", {"checked_at": _luc(tuoi_rut),
                                                  "ket_qua": {"doi:10.1000/d4": {"status": rut_doi}}})
    return d


def _tra(doi):
    return CROSSREF.get(doi)


def _so(kq, so):
    return next(x for x in kq["tltk"] if x["so"] == so)


# ── trước khi bác sĩ cho giữ: luật toàn văn nguyên vẹn ──────────────────────────────────────────────────────────
def test_chua_co_tep_giu_thi_khong_lay_duoc_van_bi_chan(tmp_path):
    d = _de_tai(tmp_path)
    kq = TVT.danh_gia(d, S)
    assert kq["trang_thai"] == "VI_PHAM" and kq["giu_tep"] is None
    assert TVT.tieu_chi_g10(d, S)[0] == "BLOCK"


# ── đề xuất: đo đủ ba tiêu chí ──────────────────────────────────────────────────────────────────────────────────
def test_de_xuat_giu_do_du_ba_tieu_chi_cho_moi_loai_nguon(tmp_path):
    d = _de_tai(tmp_path)
    dx = TVT.de_xuat_giu(d, S, tra_doi=_tra)
    loai = {x["so"]: x["loai_nguon"] for x in dx["giu"]}
    assert loai == {1: "bai_tap_chi", 3: "van_ban_phap_quy", 4: "bai_tap_chi", 5: "tai_lieu_to_chuc_quoc_te"}
    assert dx["khong_dat"] == []
    for x in dx["giu"]:
        assert set(x["tieu_chi"]) == {"dinh_danh", "rut_bai", "loai_nguon"}
        assert all(v["dat"] for v in x["tieu_chi"].values())


def test_khong_mang_thi_tltk_chi_co_doi_khong_dat(tmp_path):
    d = _de_tai(tmp_path)
    dx = TVT.de_xuat_giu(d, S, tra_doi=None)
    assert 4 not in {x["so"] for x in dx["giu"]}
    assert any(x["so"] == 4 and "Crossref" in x["ly_do"] for x in dx["khong_dat"])


def test_tien_an_pham_khong_dat_loai_nguon(tmp_path):
    d = _de_tai(tmp_path)

    def tra(doi):
        return {**CROSSREF[doi], "type": "posted-content", "container-title": ["medRxiv"]}

    dx = TVT.de_xuat_giu(d, S, tra_doi=tra)
    assert any(x["so"] == 4 and "loai_nguon" in x["ly_do"] for x in dx["khong_dat"])


def test_doi_lech_tieu_de_hoac_nam_khong_dat_dinh_danh(tmp_path):
    d = _de_tai(tmp_path)
    for sai in ({"title": ["Một bài hoàn toàn khác về tim mạch"]}, {"issued": {"date-parts": [[2019]]}}):
        dx = TVT.de_xuat_giu(d, S, tra_doi=lambda doi, sai=sai: {**CROSSREF[doi], **sai})
        assert any(x["so"] == 4 and "dinh_danh" in x["ly_do"] for x in dx["khong_dat"]), sai


def test_van_ban_khong_nhan_dien_duoc_co_quan_thi_khong_dat():
    so = {"meta": {}, "rut": {}}
    for van in ("Trang web Sức khỏe ABC. Hướng dẫn chăm sóc. 2020.",
                "Nguyễn Văn A. Bài giảng nội bộ khoa. Hà Nội; 2019."):
        tc = TVT.tieu_chuan_trich_dan(sorted(TVT.khoa_tltk(van)), van, so)
        assert not tc["dat"] and tc["loai_nguon"] is None, van


def test_pmid_chua_phan_giai_trong_a12_khong_dat(tmp_path):
    d = _de_tai(tmp_path, meta=False)
    dx = TVT.de_xuat_giu(d, S, tra_doi=_tra)
    assert any(x["so"] == 1 and "dinh_danh" in x["ly_do"] for x in dx["khong_dat"])


# ── ghi: bắt buộc lời bác sĩ ──────────────────────────────────────────────────────────────────────────────────────
def test_ap_dung_giu_bat_buoc_loi_bac_si(tmp_path):
    d = _de_tai(tmp_path)
    for loi in ("", "   ", None):
        try:
            TVT.ap_dung_giu(d, S, loi, tra_doi=_tra)
        except ValueError:
            continue
        raise AssertionError(f"phải từ chối lời rỗng {loi!r}")
    assert not (d / TVT.TEP_GIU.format(study=S)).exists()


def test_cli_giu_chuan_ap_dung_thieu_loi_tra_ma_3(tmp_path):
    _de_tai(tmp_path)
    assert TVT.main(["giu-chuan", "--study", S, "--ap-dung", "--khong-mang"], exports=tmp_path) == 3


# ── cổng sau khi giữ ────────────────────────────────────────────────────────────────────────────────────────────
def test_sau_khi_giu_cong_dat_co_giu_va_neu_ro_tltk_giu(tmp_path):
    d = _de_tai(tmp_path)
    kq_ghi = TVT.ap_dung_giu(d, S, LOI, tra_doi=_tra)
    assert kq_ghi["da_ghi"] == 4
    luu = json.loads((d / TVT.TEP_GIU.format(study=S)).read_text(encoding="utf-8"))
    assert luu["loi_bac_si"] == LOI and luu["schema"] == TVT.SCHEMA_GIU and luu["study"] == S
    kq = TVT.danh_gia(d, S)
    assert kq["trang_thai"] == "DAT_CO_GIU" and kq["dem"]["giu_giu"] == 4
    trang, bang = TVT.tieu_chi_g10(d, S)
    assert trang == "PASS"
    assert "được giữ" in bang and "TLTK 1, 3, 4, 5" in bang  # không trông như mọi bài có toàn văn
    assert TVT.main(["kiem", "--study", S], exports=tmp_path) == 0


def test_bai_giu_bi_rut_thi_mat_quyen_giu_va_chan(tmp_path):
    d = _de_tai(tmp_path)
    TVT.ap_dung_giu(d, S, LOI, tra_doi=_tra)
    _ghi(d / "A12_RETRACTION_RECEIPT.json", {"checked_at_utc": _luc(1),
                                             "results": {"11111111": {"status": "retracted"}}})
    kq = TVT.danh_gia(d, S)
    assert _so(kq, 1)["giu"] == "vo_hieu" and kq["trang_thai"] == "VI_PHAM"
    trang, bang = TVT.tieu_chi_g10(d, S)
    assert trang == "BLOCK" and "TLTK 1" in bang and "ĐÃ BỊ RÚT" in bang


def test_bai_giu_chi_doi_bi_rut_theo_so_kiem_cung_mat_quyen(tmp_path):
    d = _de_tai(tmp_path)
    TVT.ap_dung_giu(d, S, LOI, tra_doi=_tra)
    _ghi(d / f"KIEM_RUT_BAI_TRICH_DAN_{S}.json", {"checked_at": _luc(1),
                                                  "ket_qua": {"doi:10.1000/d4": {"status": "expression_of_concern"}}})
    kq = TVT.danh_gia(d, S)
    # TLTK 4 còn làn chưa thử: bị rút thì vẫn là VI PHẠM (không chỉ «còn việc»)
    assert _so(kq, 4)["giu"] == "vo_hieu" and _so(kq, 4)["ket_luan"] == "chua_thu_het"
    assert kq["trang_thai"] == "VI_PHAM" and TVT.tieu_chi_g10(d, S)[0] == "BLOCK"


def test_kiem_rut_bai_qua_han_thi_cho_kiem_lai_khong_dat(tmp_path):
    d = _de_tai(tmp_path)
    TVT.ap_dung_giu(d, S, LOI, tra_doi=_tra)
    for p, khoa in ((d / "A12_RETRACTION_RECEIPT.json", "checked_at_utc"), (d / f"KIEM_RUT_BAI_TRICH_DAN_{S}.json",
                                                                            "checked_at")):
        x = json.loads(p.read_text(encoding="utf-8"))
        x[khoa] = _luc(TVT.HAN_RUT_BAI_NGAY + 5)
        _ghi(p, x)
    kq = TVT.danh_gia(d, S)
    assert _so(kq, 1)["giu"] == "cho_kiem" and _so(kq, 4)["giu"] == "cho_kiem"
    assert _so(kq, 3)["giu"] == "giu"  # văn bản quy phạm: rút bài không áp dụng
    assert kq["trang_thai"] == "CON_VIEC"
    trang, bang = TVT.tieu_chi_g10(d, S)
    assert trang == "REVIEW" and "quá hạn" in bang


def test_tep_giu_thieu_loi_bac_si_hoac_sai_de_tai_thi_khong_giu(tmp_path):
    d = _de_tai(tmp_path)
    TVT.ap_dung_giu(d, S, LOI, tra_doi=_tra)
    p = d / TVT.TEP_GIU.format(study=S)
    goc = json.loads(p.read_text(encoding="utf-8"))
    for sua, chu in (({"loi_bac_si": " "}, "lời bác sĩ"), ({"study": "DE-TAI-KHAC"}, "sai khuôn"),
                     ({"schema": "khac/v1"}, "sai khuôn")):
        _ghi(p, {**goc, **sua})
        kq = TVT.danh_gia(d, S)
        assert kq["trang_thai"] == "VI_PHAM" and kq["dem"]["giu_giu"] == 0, sua
        assert any(chu in e for e in kq["loi"]), sua


def test_cong_do_lai_khong_tin_loi_khai_cua_tep_giu(tmp_path):
    """Tệp giữ ghi «đạt» nhưng biên nhận A12 không còn PMID ⇒ cổng đo lại ⇒ không đạt, vẫn chặn."""
    d = _de_tai(tmp_path)
    TVT.ap_dung_giu(d, S, LOI, tra_doi=_tra)
    (d / "A12_METADATA_RECEIPT.json").unlink()
    kq = TVT.danh_gia(d, S)
    assert _so(kq, 1)["giu"] == "khong_dat" and kq["trang_thai"] == "VI_PHAM"


def test_tltk_chi_doi_can_bang_chung_crossref_trong_tep_giu(tmp_path):
    d = _de_tai(tmp_path)
    TVT.ap_dung_giu(d, S, LOI, tra_doi=_tra)
    p = d / TVT.TEP_GIU.format(study=S)
    goc = json.loads(p.read_text(encoding="utf-8"))
    for m in goc["muc"]:
        if m["so"] == 4:
            m["tieu_chi"]["dinh_danh"]["dat"] = False
    _ghi(p, goc)
    assert _so(TVT.danh_gia(d, S), 4)["giu"] == "khong_dat"


def test_loai_bo_bo_qua_tltk_duoc_giu(tmp_path):
    d = _de_tai(tmp_path)
    assert {x["pmid"] for x in TVT.de_xuat_loai_bo(d, S)["loai"]} == {"11111111"}
    TVT.ap_dung_giu(d, S, LOI, tra_doi=_tra)
    dx = TVT.de_xuat_loai_bo(d, S)
    assert dx["loai"] == [] and dx["sua_tay"] == []


def test_gop_rut_bat_doi_xung_duong_tinh_thang_ban_moi_hon():
    ok_moi = ("ok", "a", 1)
    rut_cu = ("retracted", "b", 200)
    assert TVT._gop_rut(ok_moi, rut_cu) == rut_cu and TVT._gop_rut(rut_cu, ok_moi) == rut_cu
    assert TVT._gop_rut(("ok", "a", 40), ("ok", "b", 3)) == ("ok", "b", 3)
    assert TVT._gop_rut(("ok", "a", 3), ("unknown", "b", 0)) == ("ok", "a", 3)


def test_ten_noi_xuat_ban_crossref_duoc_giai_ma_html():
    so = {"meta": {}, "rut": {"doi:10.1/x": ("ok", "sổ", 1)}}
    van = "Browne MW. Alternative ways of assessing model fit. Sociol Methods Res. 1992. doi:10.1/x."
    tc = TVT.tieu_chuan_trich_dan(["doi:10.1/x"], van, so, tra_doi=lambda doi: {
        "title": ["Alternative ways of assessing model fit"], "issued": {"date-parts": [[1992]]},
        "type": "journal-article", "container-title": ["Sociological Methods &amp; Research"]})
    assert tc["dat"] and "Sociological Methods & Research" in tc["tieu_chi"]["loai_nguon"]["mo_ta"]


def test_ban_tien_in_medrxiv_co_pmid_khong_dat_loai_nguon(tmp_path):
    """PubMed lập chỉ mục bản tiền in medRxiv với tên tạp chí «medRxiv : the preprint server…» — chưa bình duyệt."""
    d = _de_tai(tmp_path)
    p = d / "A12_METADATA_RECEIPT.json"
    x = json.loads(p.read_text(encoding="utf-8"))
    x["metadata"]["11111111"]["journal"] = "medRxiv : the preprint server for health sciences"
    _ghi(p, x)
    dx = TVT.de_xuat_giu(d, S, tra_doi=_tra)
    assert any(y["so"] == 1 and "loai_nguon" in y["ly_do"] for y in dx["khong_dat"])


def test_bai_da_o_loai_bo_khong_duoc_giu_lai(tmp_path):
    d = _de_tai(tmp_path)
    TVT.ap_dung_giu(d, S, LOI, tra_doi=_tra)
    _ghi(d / f"DANH_MUC_TRICH_DAN_{S}.json", {"schema": "de_tai/danh_muc_trich_dan/v1", "study": S, "trich_dan": [],
                                              "loai_bo": [{"pmid": "11111111", "ly_do": "bác sĩ loại"}]})
    kq = TVT.danh_gia(d, S)
    assert _so(kq, 1)["giu"] is None and _so(kq, 1)["da_loai_bo"] and kq["trang_thai"] == "VI_PHAM"


def test_pmid_a12_ghi_khong_phan_giai_thi_khong_dat(tmp_path):
    d = _de_tai(tmp_path)
    p = d / "A12_METADATA_RECEIPT.json"
    x = json.loads(p.read_text(encoding="utf-8"))
    x["metadata"]["11111111"]["status"] = "not_found"
    _ghi(p, x)
    dx = TVT.de_xuat_giu(d, S, tra_doi=_tra)
    assert any(y["so"] == 1 and "dinh_danh" in y["ly_do"] for y in dx["khong_dat"])


def test_pmid_lech_doi_va_lech_tieu_de_thi_khong_dat(tmp_path):
    """PMID trỏ sang bài khác (DOI PubMed khác DOI của câu TLTK, tiêu đề không khớp) ⇒ không đạt định danh."""
    d = _de_tai(tmp_path)
    p = d / "A12_METADATA_RECEIPT.json"
    x = json.loads(p.read_text(encoding="utf-8"))
    x["metadata"]["11111111"].update(doi="10.9999/khac", title="Cardiac rehabilitation after myocardial infarction")
    _ghi(p, x)
    dx = TVT.de_xuat_giu(d, S, tra_doi=_tra)
    assert any(y["so"] == 1 and "khớp tiêu đề" in y["ly_do"] for y in dx["khong_dat"])
