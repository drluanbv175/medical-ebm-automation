"""Khứ hồi từng ô của `xuat-sav` (E3), kiểm từ điển .sav (E2 phía SPSS) và .rds có nhãn + kiểm ba chiều (E2 phía R).

Không cần SPSS/R: tests/fixtures/spss_khu_hoi/ là dữ liệu GIẢ (không PII) cùng đầu ra THẬT của SPSS 31.0.1
(`spss_chay_nen.py --du-lieu`) và R 4.6.2 (script `xuat-rds` sinh ra) chạy trên chính tệp đó ngày 14/11/2026; lượt chạy
SPSS/R được giả lập bằng cách chép các tệp xả đó (có thể làm hỏng có chủ đích). Test chạy SPSS/R THẬT tự bỏ qua khi máy
không có phần mềm; test R thật chỉ cần BASE R (CI không có jsonlite/haven).
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import cau_noi_r as R  # noqa: E402
import cau_noi_spss as C  # noqa: E402
import spss_chay_nen as N  # noqa: E402

FX = Path(__file__).resolve().parent / "fixtures" / "spss_khu_hoi"
# biến môi trường EBM_SPSS_PYTHON/EBM_RSCRIPT được trả nguyên (không kiểm tồn tại) ⇒ tự kiểm tệp có thật
CO_SPSS = any(p.is_file() for p in C.ung_vien_python_spss())
CO_R = any(p.is_file() for p in R.ung_vien_rscript())


def _ke(tmp_path: Path | None = None, csv_p: Path | None = None) -> tuple[Path, list[dict]]:
    p = csv_p or FX / "du_lieu.csv"
    tieu_de, tk, _ = C.quet_csv(p)
    ke, _, _ = C.ke_hoach_bien(tieu_de, tk, C.doc_tu_dien(FX / "tu_dien.csv"), C.doc_ma_thieu(FX / "ma_thieu.csv"))
    return p, ke


def _dl() -> dict:
    return json.loads((FX / "spss_du_lieu.json").read_text(encoding="utf-8"))


def _td() -> dict:
    return json.loads((FX / "spss_tu_dien.json").read_text(encoding="utf-8"))


def _b(ke: list[dict], ten: str) -> dict:
    return next(b for b in ke if b["ten"] == ten)


# ───────────── E3: giá trị kỳ vọng + so từng ô ─────────────


def test_khu_hoi_dau_ra_spss_that_khop_tung_o():
    p, ke = _ke()
    dl = _dl()
    kq = C.so_sanh_gia_tri(p, ke, dl["bien"], dl["ca"])
    assert kq["trang_thai"] == "KHOP" and kq["so_o"] == 80 and kq["so_lech"] == 0, kq["mau_lech"]
    # «007» ⇒ 7: không phải lệch (pandas cũng đọc 7) nhưng có ghi chú tư vấn
    assert any("số 0 đứng đầu" in g and "chi_so" in g for g in kq["ghi_chu"])


def test_gia_tri_ky_vong_theo_luat_get_data_da_do():
    _, ke = _ke()
    tuoi, hut, ghi, nghe = _b(ke, "Tuoi"), _b(ke, "hut_thuoc"), _b(ke, "ghi"), _b(ke, "nghe")
    assert C.gia_tri_ky_vong(tuoi, " 72 ") == 72.0 and C.gia_tri_ky_vong(tuoi, "") is None
    assert C.gia_tri_ky_vong(tuoi, "   ") is None and C.gia_tri_ky_vong(tuoi, None) is None  # dòng thiếu ô
    assert C.gia_tri_ky_vong(hut, "BTR") == -9991.0  # mã thiếu chữ ⇒ mã số thay như RECODE của .sps
    assert C.gia_tri_ky_vong(ghi, "  có dấu  ") == "  có dấu"  # SPSS giữ khoảng trắng ĐẦU, bỏ dấu cách CUỐI
    assert C.gia_tri_ky_vong(nghe, None) == ""


def test_so_lech_ulp_dung_nguong_da_do():
    # SPSS 31 và R 4.6.2 đọc số lệch float() của Python tới 6 ulp (đo 3000 + 6800 số) ⇒ ngưỡng 8 ulp
    a = 0.41817215137075947
    assert C._khop_so(a, a + 6 * math.ulp(a)) and C._khop_so(-906834.6387644875, -906834.6387644876)
    assert not C._khop_so(a, a + 9 * math.ulp(a))
    assert not C._khop_so(123456.789, 123456.79)  # mất chữ số thật ⇒ lệch
    assert not C._khop_so(1.0, None) and C._khop_so(None, None) and C._khop_so(-0.0, 0.0)


def test_bat_cat_cut_chuoi_va_che_gia_tri_chu_tu_do():
    p, ke = _ke()
    dl = _dl()
    j = dl["bien"].index("ghi")
    dl["ca"][0][j] = dl["ca"][0][j][:10]  # «  Đau đầu nhẹ, buổi sáng» bị cắt như A quá hẹp
    kq = C.so_sanh_gia_tri(p, ke, dl["bien"], dl["ca"])
    assert kq["trang_thai"] == "LECH" and kq["so_lech"] == 1
    m = kq["mau_lech"][0]
    assert m["ca"] == 1 and m["bien"] == "ghi" and m["loai"].startswith("cắt cụt theo độ rộng")
    assert "Đau" not in json.dumps(kq, ensure_ascii=False)  # biến chữ tự do: CHE giá trị trong báo cáo
    assert m["ky_vong"].startswith("‹chuỗi")


def test_bat_hong_ma_hoa_tieng_viet_va_so_thanh_sysmis():
    p, ke = _ke()
    dl = _dl()
    jg, jc = dl["bien"].index("ghi"), dl["bien"].index("chi_so")
    goc = dl["ca"][3][jg]
    dl["ca"][3][jg] = goc.encode("utf-8").decode("cp1252", errors="replace")
    dl["ca"][5][jc] = None  # «007» đọc thành SYSMIS
    kq = C.so_sanh_gia_tri(p, ke, dl["bien"], dl["ca"])
    loai = {m["bien"]: m["loai"] for m in kq["mau_lech"]}
    assert kq["so_lech"] == 2 and "hỏng mã hoá" in loai["ghi"] and loai["chi_so"].startswith("mất số")
    assert kq["lech_theo_bien"] == {"ghi": 1, "chi_so": 1}


def test_bat_moi_cot_khong_bo_sot_cot_nao():
    p, ke = _ke()
    for j, ten in enumerate(_dl()["bien"]):  # hỏng MỘT ô ở từng biến lần lượt — biến nào cũng phải bị bắt
        dl = _dl()
        x = dl["ca"][2][j]
        dl["ca"][2][j] = (x + "?") if isinstance(x, str) else (12345.0 if x is None else x + 1)
        kq = C.so_sanh_gia_tri(p, ke, dl["bien"], dl["ca"])
        assert kq["so_lech"] == 1 and kq["mau_lech"][0]["bien"] == ten, ten


def test_bat_dich_dong_va_thieu_thua_ca():
    p, ke = _ke()
    dl = _dl()
    bo = copy.deepcopy(dl)
    del bo["ca"][2]  # SPSS bỏ một dòng (dòng trống) ⇒ mọi ca sau lệch một nhịp
    kq = C.so_sanh_gia_tri(p, ke, bo["bien"], bo["ca"])
    assert kq["trang_thai"] == "LECH" and any("DỊCH DÒNG từ ca 3" in g and "BỎ" in g for g in kq["ghi_chu"])
    assert any("số ca" in g for g in kq["ghi_chu"])
    chen = copy.deepcopy(dl)
    chen["ca"].insert(4, ["dòn", None, None, None, None, None, "", "", None, None])  # ô nhiều dòng bị tách
    kq = C.so_sanh_gia_tri(p, ke, chen["bien"], chen["ca"])
    assert any("CHÈN" in g for g in kq["ghi_chu"]) and any("bản đọc lại 9 ca" in g for g in kq["ghi_chu"])
    thua = C.so_sanh_gia_tri(p, ke, dl["bien"], dl["ca"] + [list(dl["ca"][0])])  # chỉ THỪA một ca ở cuối
    assert thua["so_lech"] == 1 and thua["mau_lech"] == [
        {"ca": 9, "bien": "*", "ky_vong": "—", "nhan_duoc": "ca thừa", "loai": "thừa ca"}
    ]


def test_thieu_bien_trong_ban_doc_lai_la_lech():
    p, ke = _ke()
    dl = _dl()
    j = dl["bien"].index("hai_long")
    dl["bien"][j] = "khac_ten"
    kq = C.so_sanh_gia_tri(p, ke, dl["bien"], dl["ca"])
    assert kq["so_lech"] == 8 and any("KHÔNG có trong bản đọc lại" in g for g in kq["ghi_chu"])


def test_quet_csv_do_rong_tinh_ca_khoang_trang_dau(tmp_path):
    # đo thật: GET DATA giữ khoảng trắng đầu của ô chuỗi ⇒ độ rộng A phải chứa nó (bản cũ cắt «  Nguyễn V»)
    p = tmp_path / "d.csv"
    p.write_text('ma,ghi\n1,"  Đau đầu  "\n2,\t\t\t\n', encoding="utf-8", newline="\n")
    _, tk, _ = C.quet_csv(p)
    assert tk[1]["rong"] == len("  Đau đầu".encode())  # dấu cách CUỐI không tính (SPSS bỏ)
    p.write_text("ma,ghi\n1,x\n2,\t\t\t\n", encoding="utf-8", newline="\n")
    assert C.quet_csv(p)[1][1]["rong"] == 3  # ô chỉ có tab vẫn là chuỗi 3 byte trong SPSS


# ───────────── E2 phía SPSS: từ điển .sav ↔ kế hoạch ─────────────


def test_tu_dien_sav_that_khop_ke_hoach():
    _, ke = _ke()
    kq = C.kiem_tu_dien_sav(ke, _td())
    assert kq == {"trang_thai": "KHOP", "so_lech": 0, "lech": []}


@pytest.mark.parametrize(
    "hong, phai_co",
    [
        (lambda td: td["bien"][4]["nhan_gia_tri"].pop("9.0"), "nhãn giá trị"),  # mất nhãn mã thiếu 9
        (lambda td: td["bien"][4]["nhan_gia_tri"].update({"3.0": "Sai"}), "sai nhãn mã"),
        (lambda td: td["bien"][4].update({"thieu": [0, None, None, None]}), "MISSING VALUES"),
        (lambda td: td["bien"][5].update({"thieu": [1, -9991.0, None, None]}), None),  # đúng ⇒ không lệch
        (lambda td: td["bien"][4].update({"muc_do": "NOMINAL"}), "mức đo"),
        (lambda td: td["bien"][1].update({"nhan": "Tuổi"}), "nhãn biến"),
        (lambda td: td["bien"][2].update({"kieu": 8}), "biến SỐ"),
        (lambda td: td["bien"][7].update({"kieu": 20}), "chuỗi A39"),
        (lambda td: td["bien"].insert(0, td["bien"].pop(3)), "thứ tự"),
        (lambda td: td["bien"][6]["nhan_gia_tri"].pop("khac     "), "thiếu mã khac"),
    ],
)
def test_tu_dien_sav_bat_tung_loai_lech(hong, phai_co):
    _, ke = _ke()
    td = _td()
    hong(td)
    kq = C.kiem_tu_dien_sav(ke, td)
    if phai_co is None:
        assert kq["trang_thai"] == "KHOP"
    else:
        assert kq["trang_thai"] == "LECH" and any(phai_co in x for x in kq["lech"]), kq["lech"]


def test_thieu_tu_spss_va_ke_hoach_cung_khuon():
    assert C.thieu_tu_spss([-3, "LO", -9991.0, 9.0], True) == {"roi": [9.0], "khoang": ["LO", -9991.0]}
    b = {"so": True, "menh_de_thieu": f"LO THRU {C.MA_CHU_BAT_DAU}, 9"}
    assert C.ky_vong_thieu(b) == {"roi": [9.0], "khoang": ["LO", -9991.0]}
    assert C.thieu_tu_spss([1, "        ", None, None], False) == {"roi": [""], "khoang": None}  # đệm 8 byte


# ───────────── xuat-sav: luồng đầy đủ với SPSS giả lập (tệp xả thật) ─────────────


def _de_tai(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.setattr(C, "EXPORTS", tmp_path / "exports")
    d = tmp_path / "exports" / "THU"
    d.mkdir(parents=True)
    shutil.copy(FX / "tu_dien.csv", d / "G5_REDCap_dictionary_THU.csv")
    shutil.copy(FX / "ma_thieu.csv", d / "_ma-thieu-theo-bien.csv")
    return d


def _ns(**kw) -> argparse.Namespace:
    d = {"study": "THU", "data": str(FX / "du_lieu.csv"), "ban_nhap": True, "dictionary": None, "ma_thieu": None}
    d.update(kw)
    return argparse.Namespace(**d)


def _spss_gia(monkeypatch, *, sua_dl=None, sua_td=None, ma_doc=0):
    goi: list[str] = []

    def gia(py, doi_so, *, thu_muc, thoi_han=0):
        goi.append(doi_so[0])
        if doi_so[0] == "--cu-phap":
            (thu_muc / "ra.sav").write_bytes(b"$FL2 gia")
            return 0, "PHIEN_BAN=31.0\nSO_CA=8\n", ""
        assert doi_so[0] == "--du-lieu" and Path(doi_so[1]).parent == thu_muc  # đọc lại TRONG vùng tạm
        if ma_doc:
            return ma_doc, "", "LOI_SPSS hỏng"
        dl, td = _dl(), _td()
        if sua_dl:
            sua_dl(dl)
        if sua_td:
            sua_td(td)
        Path(doi_so[2]).write_text(json.dumps(dl, ensure_ascii=False), encoding="utf-8", newline="\n")
        Path(doi_so[3]).write_text(json.dumps(td, ensure_ascii=False), encoding="utf-8", newline="\n")
        return 0, "PHIEN_BAN=31.0\nSO_CA_DOC=8\nSO_CA=8\n", ""

    monkeypatch.setattr(C, "tim_spss", lambda: Path("python-cua-spss"))
    monkeypatch.setattr(C, "chay_spss", gia)
    return goi


def test_xuat_sav_khop_ghi_khu_hoi_vao_manifest(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch)
    goi = _spss_gia(monkeypatch)
    assert C.lenh_xuat_sav(_ns()) == C.MA_OK
    assert goi == ["--cu-phap", "--du-lieu"]
    man = json.loads((d / "spss" / "THU_BAN-NHAP.sav.manifest.json").read_text(encoding="utf-8"))
    assert man["sav_da_tao"] and (d / "spss" / "THU_BAN-NHAP.sav").is_file()
    kh = man["khu_hoi"]
    assert (kh["trang_thai"], kh["so_o"], kh["so_lech"]) == ("KHOP", 80, 0) and kh["luc"]
    assert man["kiem_tu_dien"]["trang_thai"] == "KHOP"
    assert "đọc lại .sav" in (d / "spss" / "THU_nhan_bien_ban-nhap.log").read_text(encoding="utf-8")


def test_xuat_sav_lech_tung_o_bo_tep_va_ma_1(tmp_path, monkeypatch, capsys):
    d = _de_tai(tmp_path, monkeypatch)

    def cat(dl):
        dl["ca"][3][dl["bien"].index("ghi")] = "Việt Nam — tiế"

    _spss_gia(monkeypatch, sua_dl=cat)
    assert C.lenh_xuat_sav(_ns()) == C.MA_LECH
    assert not (d / "spss" / "THU_BAN-NHAP.sav").exists()  # tệp hỏng KHÔNG được nhận
    man = json.loads((d / "spss" / "THU_BAN-NHAP.sav.manifest.json").read_text(encoding="utf-8"))
    assert not man["sav_da_tao"] and man["khu_hoi"]["trang_thai"] == "LECH" and man["khu_hoi"]["so_lech"] == 1
    ra = capsys.readouterr().out
    assert "ca 4 · ghi" in ra and "cắt cụt" in ra and "Việt Nam" not in ra  # giá trị chữ tự do bị che


def test_xuat_sav_lech_tu_dien_bo_tep_va_ma_1(tmp_path, monkeypatch, capsys):
    d = _de_tai(tmp_path, monkeypatch)
    _spss_gia(monkeypatch, sua_td=lambda td: td["bien"][4].update({"thieu": [0, None, None, None]}))
    assert C.lenh_xuat_sav(_ns()) == C.MA_LECH
    assert not (d / "spss" / "THU_BAN-NHAP.sav").exists()
    man = json.loads((d / "spss" / "THU_BAN-NHAP.sav.manifest.json").read_text(encoding="utf-8"))
    assert man["kiem_tu_dien"]["trang_thai"] == "LECH" and man["khu_hoi"]["trang_thai"] == "KHOP"
    assert "MISSING VALUES" in capsys.readouterr().out


def test_xuat_sav_khong_doc_lai_duoc_la_ma_1_khong_nhan_tep(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch)
    _spss_gia(monkeypatch, ma_doc=1)
    assert C.lenh_xuat_sav(_ns()) == C.MA_LECH
    assert not (d / "spss" / "THU_BAN-NHAP.sav").exists()
    man = json.loads((d / "spss" / "THU_BAN-NHAP.sav.manifest.json").read_text(encoding="utf-8"))
    assert man["khu_hoi"]["trang_thai"] == "LOI" and "không đọc lại" in man["khu_hoi"]["ly_do"]


def test_xuat_sav_cu_khong_song_sot_qua_luot_lech(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch)
    _spss_gia(monkeypatch)
    assert C.lenh_xuat_sav(_ns()) == C.MA_OK
    _spss_gia(monkeypatch, sua_dl=lambda dl: dl["ca"][0].__setitem__(1, 51.0))
    assert C.lenh_xuat_sav(_ns()) == C.MA_LECH
    assert not (d / "spss" / "THU_BAN-NHAP.sav").exists()  # .sav của lượt trước cũng đã bị gỡ
    with pytest.raises(C.KhongDoDuoc):
        C._doc_manifest_sav("THU")  # các lệnh sau (chay/doi-chieu) không dùng được tệp chưa qua khứ hồi


# ───────────── trình chạy nền: giá trị thô ─────────────


def test_trinh_chay_nen_gia_tri_tho_va_tham_so():
    assert N.gia_tri_tho(None) is None and N.gia_tri_tho(0.1) == 0.1
    assert N.gia_tri_tho("A1   ") == "A1" and N.gia_tri_tho("  x\t ") == "  x\t"  # chỉ bỏ dấu cách ĐỆM bên phải
    assert N.gia_tri_tho(b"Vi\xe1\xbb\x87t  ") == "Việt" and N.gia_tri_tho(b"\xe1\xbb") == "�"
    assert N.gia_tri_tho(float("nan")) is None
    assert json.loads(json.dumps(N.gia_tri_tho(0.41817215137075947))) == 0.41817215137075947  # đọc lại đúng từng bit
    assert N.main(["--du-lieu", "x.sav"]) == 2  # thiếu tệp ra — kiểm TRƯỚC khi import spss


# ───────────── E2 phía R: .rds có nhãn ─────────────


def test_chuoi_r_u_thuan_ascii_ca_ky_tu_ngoai_bmp():
    s = R.chuoi_r_u('Việt "x" \\ \n 😀')
    assert s.isascii() and s == '"Vi\\U{1ec7}t \\"x\\" \\\\ \\x0a \\U{1f600}"'


def test_script_rds_chi_dung_base_r_va_thay_mot_luot(tmp_path):
    p, ke = _ke()
    vb = R.sinh_script_rds("THU", p, tmp_path / "x.rds", "ab" * 32, C.quet_csv(p)[0], ke, ban_nhap=True)
    thi_hanh = "\n".join(d.split("  # ")[0] for d in vb.splitlines() if not d.lstrip().startswith("#"))
    assert thi_hanh.isascii()  # chuỗi R đã thoát \U{…}: Rscript ở locale C vẫn đọc đúng tiếng Việt (đo thật)
    assert "@@" not in thi_hanh and "jsonlite" not in thi_hanh
    assert "library(" not in thi_hanh and "haven::" in thi_hanh  # haven CHỈ ở chặng .sav ↔ .rds, có rào
    assert 'requireNamespace("haven", quietly = TRUE)' in thi_hanh
    assert "fill = TRUE, flush = TRUE, blank.lines.skip = FALSE" in thi_hanh  # như SPSS: thiếu/thừa ô
    assert "read.csv" not in thi_hanh and "fileEncoding" not in thi_hanh  # locale C làm hỏng tiếng Việt (đo thật)
    ke2 = copy.deepcopy(ke)
    ke2[0]["nhan"] = "@@KE@@ quit()"
    vb2 = R.sinh_script_rds("THU", p, tmp_path / "x.rds", "ab" * 32, C.quet_csv(p)[0], ke2, ban_nhap=True)
    assert vb2.count("quit(save") == vb.count("quit(save")  # tên/nhãn không tiêm được mã R


def test_doc_ban_xa_r_that():
    b, ca, tt = R.doc_ban_xa_r(FX / "r_gia_tri.txt", FX / "r_thuoc_tinh.txt")
    assert b[0] == "ID" and len(ca) == 8 and ca[0][b.index("ghi")] == "  Đau đầu nhẹ, buổi sáng"
    assert ca[1][b.index("hut_thuoc")] == -9991.0 and ca[6][b.index("trieu_chung___1")] is None
    assert ca[2][b.index("ghi")] == ""  # «» khác NA
    assert tt["hai_long"]["class"] == R.LOP_SO_NHAN and tt["hai_long"]["na_values"] == [9.0]
    assert tt["hut_thuoc"]["gt"][-9991.0] == "BTR — Bỏ trống"
    assert tt["nghe"]["class"] == R.LOP_CHU_NHAN and tt["nghe"]["gt"]["khac"] == "Khác"
    assert tt["Tuoi"]["class"] == ["numeric"] and tt["ghi"]["class"] == ["character"]


def test_khu_hoi_va_thuoc_tinh_rds_that_khop():
    p, ke = _ke()
    b, ca, tt = R.doc_ban_xa_r(FX / "r_gia_tri.txt", FX / "r_thuoc_tinh.txt")
    assert C.so_sanh_gia_tri(p, ke, b, ca)["trang_thai"] == "KHOP"
    assert R.kiem_thuoc_tinh_rds(ke, b, tt) == {"trang_thai": "KHOP", "so_lech": 0, "lech": []}
    sav = R.doc_ban_xa_r(FX / "sav_gia_tri.txt", FX / "sav_thuoc_tinh.txt")
    assert R.so_sav_rds(ke, sav, (b, ca, tt))["trang_thai"] == "KHOP"


@pytest.mark.parametrize(
    "hong, phai_co",
    [
        (lambda tt: tt["hai_long"].update({"na_values": []}), "na_values"),
        (lambda tt: tt["hut_thuoc"].update({"na_values": [], "na_range": [float("-inf"), -9991.0]}), "na_range"),
        (lambda tt: tt["hai_long"]["gt"].pop(9.0), "nhãn giá trị"),
        (lambda tt: tt["Tuoi"].update({"nhan": "Tuổi"}), "nhãn biến"),
        (lambda tt: tt["nghe"].update({"class": ["character"]}), "kiểu/lớp"),
        (lambda tt: tt["chi_so"].update({"typeof": "character"}), "kiểu/lớp"),
    ],
)
def test_thuoc_tinh_rds_bat_tung_loai_lech(hong, phai_co):
    _, ke = _ke()
    b, _, tt = R.doc_ban_xa_r(FX / "r_gia_tri.txt", FX / "r_thuoc_tinh.txt")
    hong(tt)
    kq = R.kiem_thuoc_tinh_rds(ke, b, tt)
    assert kq["trang_thai"] == "LECH" and any(phai_co in x for x in kq["lech"]), kq["lech"]


def test_ba_chieu_sav_rds_bat_lech_gia_tri_va_nhan():
    _, ke = _ke()
    rds = R.doc_ban_xa_r(FX / "r_gia_tri.txt", FX / "r_thuoc_tinh.txt")
    b, ca, tt = copy.deepcopy(R.doc_ban_xa_r(FX / "sav_gia_tri.txt", FX / "sav_thuoc_tinh.txt"))
    ca[4][b.index("Tuoi")] = 45.0
    tt["gioitinh"]["gt"][1.0] = "Nữ"
    kq = R.so_sav_rds(ke, (b, ca, tt), rds)
    assert kq["trang_thai"] == "LECH" and kq["so_lech_o"] == 1
    assert any("Tuoi: 1 ô" in x for x in kq["lech"]) and any("gioitinh: nhãn giá trị" in x for x in kq["lech"])
    b2, ca2, tt2 = copy.deepcopy(R.doc_ban_xa_r(FX / "sav_gia_tri.txt", FX / "sav_thuoc_tinh.txt"))
    tt2["ID"]["na_values"] = ["", "x"]  # mã thiếu CHUỖI không mang sang .rds ⇒ không so (đã ghi trong tài liệu)
    assert R.so_sav_rds(ke, (b2, ca2, tt2), rds)["trang_thai"] == "KHOP"


# ───────────── xuat-rds: luồng đầy đủ với R giả lập (tệp xả thật) ─────────────


def _r_gia(monkeypatch, *, sua=None, ma=0, haven=True):
    goi: list[list[str]] = []

    def gia(rs, doi_so, *, thu_muc, thoi_han=0):
        goi.append(doi_so)
        if ma:
            return ma, "", "LOI_R hỏng"
        Path(doi_so[2]).write_bytes(b"RDS3 gia")
        gt, tt = (FX / "r_gia_tri.txt").read_text(encoding="ascii"), (FX / "r_thuoc_tinh.txt").read_text("ascii")
        if sua:
            gt, tt = sua(gt, tt)
        Path(doi_so[3]).write_text(gt, encoding="ascii", newline="\n")
        Path(doi_so[4]).write_text(tt, encoding="ascii", newline="\n")
        out = "PHIEN_BAN=R version 4.6.2 (2026-10-29)\nDA_GHI=8\n"
        if doi_so[5]:
            shutil.copy(FX / "sav_gia_tri.txt", doi_so[6])
            shutil.copy(FX / "sav_thuoc_tinh.txt", doi_so[7])
            out += "HAVEN=2.5.5\n" if haven else "HAVEN=\n"
        return 0, out + "XONG_RDS\n", ""

    monkeypatch.setattr(R, "tim_r", lambda: Path("Rscript"))
    monkeypatch.setattr(R, "chay_r", gia)
    return goi


def _ns_r(**kw) -> list[str]:
    a = ["xuat-rds", "--study", "THU", "--data", str(FX / "du_lieu.csv"), "--ban-nhap"]
    for k, v in kw.items():
        a += [f"--{k}", v] if v is not True else [f"--{k}"]
    return a


def test_xuat_rds_khop_khong_co_sav_chang_ba_chua_do(tmp_path, monkeypatch, capsys):
    d = _de_tai(tmp_path, monkeypatch)
    goi = _r_gia(monkeypatch)
    assert R.main(_ns_r()) == R.MA_OK
    assert goi[0][5] == ""  # chưa có .sav ⇒ không truyền
    rds = d / "r" / "THU_BAN-NHAP.rds"
    man = json.loads((d / "r" / "THU_BAN-NHAP.rds.manifest.json").read_text(encoding="utf-8"))
    assert rds.is_file() and man["rds_da_tao"] and man["sha256_rds"] == C.sha256_tep(rds)
    assert man["sha256_nguon"] == C.sha256_tep(FX / "du_lieu.csv") and man["r_phien_ban"].startswith("R version")
    assert man["ba_chieu"] == {"tu_dien_sav": "CHUA_DO", "tu_dien_rds": "KHOP", "khu_hoi_rds": "KHOP",
                               "sav_rds": "CHUA_DO"}  # fmt: skip
    assert man["khu_hoi"]["so_o"] == 80 and len(man["ke_hoach"]) == 10
    assert (d / "r" / "THU_xuat_rds_ban-nhap.R").is_file() and "chưa đo" in capsys.readouterr().out


def test_xuat_rds_ba_chieu_dung_sav_cung_ke_hoach(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch)
    _spss_gia(monkeypatch)
    assert C.lenh_xuat_sav(_ns()) == C.MA_OK
    goi = _r_gia(monkeypatch)
    assert R.main(_ns_r()) == R.MA_OK
    assert goi[0][5] == str(d / "spss" / "THU_BAN-NHAP.sav").replace("\\", "/")
    man = json.loads((d / "r" / "THU_BAN-NHAP.rds.manifest.json").read_text(encoding="utf-8"))
    assert man["ba_chieu"] == {"tu_dien_sav": "KHOP", "tu_dien_rds": "KHOP", "khu_hoi_rds": "KHOP", "sav_rds": "KHOP"}
    assert man["haven_phien_ban"] == "2.5.5"
    _r_gia(monkeypatch, haven=False)  # máy không có haven ⇒ chặng .sav ↔ .rds «chưa đo», không phải «khớp»
    assert R.main(_ns_r()) == R.MA_OK
    man = json.loads((d / "r" / "THU_BAN-NHAP.rds.manifest.json").read_text(encoding="utf-8"))
    assert man["ba_chieu"]["sav_rds"] == "CHUA_DO" and "haven" in man["sav_rds"]["ly_do"]


def test_xuat_rds_lech_bo_tep_va_ma_1(tmp_path, monkeypatch, capsys):
    d = _de_tai(tmp_path, monkeypatch)

    def bo_nhan_thieu(gt, tt):  # .rds mất na_values của hai_long
        ten = "hai_long".encode().hex()
        return gt, "\n".join(x for x in tt.splitlines() if not x.startswith(f"NA_VALUES\t{ten}\t")) + "\n"

    _r_gia(monkeypatch, sua=bo_nhan_thieu)
    assert R.main(_ns_r()) == R.MA_LECH
    assert not (d / "r" / "THU_BAN-NHAP.rds").exists()
    man = json.loads((d / "r" / "THU_BAN-NHAP.rds.manifest.json").read_text(encoding="utf-8"))
    assert not man["rds_da_tao"] and man["kiem_thuoc_tinh"]["trang_thai"] == "LECH"
    assert "na_values" in capsys.readouterr().out

    def doi_so(gt, tt):  # một ô số của .rds khác nguồn
        dong = gt.splitlines()
        o = dong[5].split("\t")
        o[1] = "45"
        dong[5] = "\t".join(o)
        return "\n".join(dong) + "\n", tt

    _r_gia(monkeypatch, sua=doi_so)
    assert R.main(_ns_r()) == R.MA_LECH
    man = json.loads((d / "r" / "THU_BAN-NHAP.rds.manifest.json").read_text(encoding="utf-8"))
    assert man["khu_hoi"]["so_lech"] == 1 and man["khu_hoi"]["mau_lech"][0]["bien"] == "Tuoi"


def test_xuat_rds_khong_co_r_la_khong_do_duoc(tmp_path, monkeypatch, capsys):
    d = _de_tai(tmp_path, monkeypatch)
    monkeypatch.setattr(R, "tim_r", lambda: (_ for _ in ()).throw(R.KhongDoDuoc("không có R")))
    assert R.main(_ns_r()) == R.MA_KHONG_DO
    assert (d / "r" / "THU_xuat_rds_ban-nhap.R").is_file()  # script vẫn sinh để chạy tay trong RStudio
    man = json.loads((d / "r" / "THU_BAN-NHAP.rds.manifest.json").read_text(encoding="utf-8"))
    assert not man["rds_da_tao"] and set(man["ba_chieu"].values()) == {"KHONG_DO_DUOC"}
    assert "KHÔNG phải «đạt»" in capsys.readouterr().out


def test_xuat_rds_r_loi_va_tu_choi(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch)
    _r_gia(monkeypatch, ma=1)
    assert R.main(_ns_r()) == R.MA_LECH and not (d / "r" / "THU_BAN-NHAP.rds").exists()
    _r_gia(monkeypatch, ma=3)  # R tự kiểm SHA-256/tiêu đề lệch ⇒ từ chối
    assert R.main(_ns_r()) == R.MA_TU_CHOI
    assert R.main(["xuat-rds", "--study", "THU", "--data", str(FX / "du_lieu.csv")]) == R.MA_TU_CHOI  # thiếu --ban-nhap


# ───────────── chạy THẬT (tự bỏ qua khi máy không có phần mềm) ─────────────

DU_LIEU_HONG = "ma,so_do\nA,1\nB,1_000\nC,\t3\nD,4\n"  # Python float() nhận «1_000» và « \t3»; SPSS/R thì không


def _de_tai_hong(tmp_path: Path) -> Path:
    p = tmp_path / "hong.csv"
    p.write_text(DU_LIEU_HONG, encoding="utf-8", newline="\n")
    (tmp_path / "td.csv").write_text(
        "Variable / Field Name,Field Type,Field Label,Identifier?\nma,text,Mã,\nso_do,text,Số đo,\n",
        encoding="utf-8",
        newline="\n",
    )
    return p


@pytest.mark.skipif(not CO_SPSS, reason="máy không có IBM SPSS Statistics")
def test_that_spss_xuat_sav_khu_hoi_khop_roi_bat_hong(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch)
    assert C.lenh_xuat_sav(_ns()) == C.MA_OK
    man = json.loads((d / "spss" / "THU_BAN-NHAP.sav.manifest.json").read_text(encoding="utf-8"))
    assert man["khu_hoi"]["trang_thai"] == "KHOP" and man["khu_hoi"]["so_o"] == 80
    assert man["kiem_tu_dien"]["trang_thai"] == "KHOP"
    # ô chuỗi DÀI NHẤT có khoảng trắng đầu: độ rộng A đo trên ô đã strip() (luật cũ) làm SPSS cắt cụt ⇒ khứ hồi đỏ
    dau = tmp_path / "dau.csv"
    dau.write_text("ma,ghi\nA,   dài nhất có dấu  \nB,ngắn\n", encoding="utf-8", newline="\n")
    (tmp_path / "td_dau.csv").write_text(
        "Variable / Field Name,Field Type,Field Label,Identifier?\nma,text,Mã,\nghi,text,Ghi,\n",
        encoding="utf-8",
        newline="\n",
    )
    ns = _ns(data=str(dau), dictionary=str(tmp_path / "td_dau.csv"), ma_thieu=str(tmp_path / "khong.csv"))
    assert C.lenh_xuat_sav(ns) == C.MA_OK
    man = json.loads((d / "spss" / "THU_BAN-NHAP.sav.manifest.json").read_text(encoding="utf-8"))
    assert man["khu_hoi"]["trang_thai"] == "KHOP" and man["khu_hoi"]["so_o"] == 4
    p = _de_tai_hong(tmp_path)
    ns = _ns(data=str(p), dictionary=str(tmp_path / "td.csv"), ma_thieu=str(tmp_path / "khong.csv"))
    assert C.lenh_xuat_sav(ns) == C.MA_LECH  # SPSS đọc «1_000» và «\t3» thành SYSMIS ⇒ khứ hồi bắt
    man = json.loads((d / "spss" / "THU_BAN-NHAP.sav.manifest.json").read_text(encoding="utf-8"))
    assert man["khu_hoi"]["so_lech"] == 2 and {m["ca"] for m in man["khu_hoi"]["mau_lech"]} == {2, 3}
    assert not (d / "spss" / "THU_BAN-NHAP.sav").exists()


@pytest.mark.skipif(not CO_R, reason="máy không có Rscript")
def test_that_r_xuat_rds_chi_can_base_r_roi_bat_hong(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch)
    assert R.main(_ns_r()) == R.MA_OK
    man = json.loads((d / "r" / "THU_BAN-NHAP.rds.manifest.json").read_text(encoding="utf-8"))
    assert man["khu_hoi"]["trang_thai"] == "KHOP" and man["kiem_thuoc_tinh"]["trang_thai"] == "KHOP"
    assert man["ba_chieu"]["sav_rds"] == "CHUA_DO"  # chưa có .sav ⇒ chặng ba không đo, không «khớp» giả
    p = _de_tai_hong(tmp_path)
    a = ["xuat-rds", "--study", "THU", "--data", str(p), "--ban-nhap", "--dictionary", str(tmp_path / "td.csv"),
         "--ma-thieu", str(tmp_path / "khong.csv")]  # fmt: skip
    assert R.main(a) == R.MA_LECH  # R đọc «1_000» thành NA ⇒ khứ hồi bắt
    man = json.loads((d / "r" / "THU_BAN-NHAP.rds.manifest.json").read_text(encoding="utf-8"))
    assert {m["ca"] for m in man["khu_hoi"]["mau_lech"]} == {2} and not (d / "r" / "THU_BAN-NHAP.rds").exists()


@pytest.mark.skipif(not (CO_SPSS and CO_R), reason="cần cả SPSS và R")
def test_that_ba_chieu_tu_dien_sav_rds(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch)
    assert C.lenh_xuat_sav(_ns()) == C.MA_OK
    assert R.main(_ns_r()) == R.MA_OK
    man = json.loads((d / "r" / "THU_BAN-NHAP.rds.manifest.json").read_text(encoding="utf-8"))
    assert man["ba_chieu"]["tu_dien_sav"] == man["ba_chieu"]["tu_dien_rds"] == man["ba_chieu"]["khu_hoi_rds"] == "KHOP"
    if man.get("haven_phien_ban"):
        assert man["ba_chieu"]["sav_rds"] == "KHOP"
    else:
        assert man["ba_chieu"]["sav_rds"] == "CHUA_DO"
