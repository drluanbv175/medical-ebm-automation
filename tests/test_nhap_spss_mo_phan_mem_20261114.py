"""Nhập THẲNG trong SPSS (mẫu .sav + đọc .sav đã nhập) và mở dữ liệu thẳng trong SPSS/RStudio — 14/11/2026.

Bác sĩ chọn: «Nút Mở trong SPSS · Cài RStudio để mở R · Nhập thẳng trong SPSS». Test không cần SPSS/R: bản đọc .sav được
thay bằng hàm giả cùng cấu trúc spss_chay_nen.py --du-lieu; một test chạy SPSS thật thì tự bỏ qua khi máy không có.
Dữ liệu GIẢ, không PII.
"""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import cau_noi_spss as SP  # noqa: E402
import mo_trong_phan_mem as MO  # noqa: E402
import nhap_lieu_excel as N  # noqa: E402

STUDY = "de-tai-spss"
TD_COT = [
    "Variable / Field Name", "Form Name", "Section Header", "Field Type", "Field Label",
    "Choices, Calculations, OR Slider Labels", "Field Note", "Text Validation Type OR Show Slider Number",
    "Text Validation Min", "Text Validation Max", "Identifier?", "Branching Logic (Show field only if...)",
    "Required Field?", "Custom Alignment", "Question Number (surveys only)", "Matrix Group Name", "Matrix Ranking?",
    "Field Annotation",
]  # fmt: skip
TRUONG = [
    ("record_id", "phieu", "text", "Mã phiếu", "", "", "", "", "y"),
    ("gioitinh", "phieu", "radio", "Giới tính", "1, Nam | 2, Nữ", "", "", "", "y"),
    ("tuoi", "phieu", "text", "Tuổi", "", "integer", "18", "120", "y"),
    ("lydo", "phieu", "checkbox", "Lý do", "1, A | 2, B", "", "", "", "n"),
    ("ngay_kham", "phieu", "text", "Ngày khám", "", "date_dmy", "", "", "n"),
    ("ghi_chu", "phieu", "text", "Ghi chú", "", "", "", "", "n"),
]


@pytest.fixture()
def de_tai(tmp_path, monkeypatch) -> Path:
    monkeypatch.setattr(SP, "EXPORTS", tmp_path / "exports")
    d = tmp_path / "exports" / STUDY
    d.mkdir(parents=True)
    with open(d / f"G5_REDCap_dictionary_{STUDY}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(TD_COT)
        for ten, form, loai, nhan, lc, kt, mn, mx, bb in TRUONG:
            r = dict.fromkeys(TD_COT, "")
            r.update({TD_COT[0]: ten, TD_COT[1]: form, TD_COT[3]: loai, TD_COT[4]: nhan, TD_COT[5]: lc, TD_COT[7]: kt,
                      TD_COT[8]: mn, TD_COT[9]: mx, TD_COT[12]: bb})  # fmt: skip
            w.writerow([r[k] for k in TD_COT])
    (d / "_ma-thieu-theo-bien.csv").write_text("bien,ma,nhan\n*,BTR,Bỏ trống\n*,KDD,Không đọc được\n", encoding="utf-8",
                                               newline="\n")  # fmt: skip
    return d


def _cot(d: Path):
    mt = SP.doc_ma_thieu(d / "_ma-thieu-theo-bien.csv")
    cot, _ = N.ke_hoach_cot(N.doc_tu_dien_day_du(d / f"G5_REDCap_dictionary_{STUDY}.csv"), mt)
    return cot, mt


def _giay(y, m, d_) -> float:
    """Giá trị ngày của SPSS = số giây từ 14/10/1582 (mốc ghi CỨNG ở đây, độc lập với hằng số của công cụ)."""
    return (datetime(y, m, d_) - datetime(1582, 10, 14)).total_seconds()


def _ban_doc(cot, ca: list[list], *, dac_ta: str | None, bien: list[str] | None = None):
    """Hàm giả thay doc_lai_sav: trả (từ điển + thuộc tính tệp, dữ liệu thô) đúng khuôn spss_chay_nen.py."""
    tt = {}
    if dac_ta:
        tt = {N.TT_MAU: ["nhap_lieu_excel.py"], N.TT_DAC_TA: [dac_ta], N.TT_MA_CHU: ['{"BTR": -9991, "KDD": -9992}']}
    ten = bien or [c.ten for c in cot]
    return lambda _p: ({"so_ca": len(ca), "bien": [], "thuoc_tinh_tep": tt}, {"bien": ten, "ca": ca})


# ───────────────────────────── mẫu .sav ─────────────────────────────


def test_cu_phap_mau_sav_du_bien_nhan_ma_thieu_va_dau_van_tay(de_tai, tmp_path):
    cot, mt = _cot(de_tai)
    sps = N.cu_phap_mau_sav(cot, mt, "abc123", tmp_path / "m.sav")
    assert "INPUT PROGRAM." in sps and "END FILE." in sps  # 0 phiếu
    assert "STRING record_id (A50)" in sps and "(EDATE10)" in sps and "(A255)" in sps
    assert "MISSING VALUES tuoi (-9991, -9992)." in sps  # BTR/KDD ⇒ số thay, khai thiếu
    assert "-9991 'BTR — Bỏ trống'" in sps and "1 'Nam'" in sps
    assert "MISSING VALUES ghi_chu ('BTR', 'KDD')." in sps  # biến CHUỖI giữ mã chữ
    assert f"{N.TT_DAC_TA}('abc123')" in sps and '{"BTR": -9991, "KDD": -9992}' in sps
    assert N.ma_chu_so(mt) == {"BTR": -9991, "KDD": -9992}


def test_ten_bien_la_tu_khoa_spss_bi_tu_choi(de_tai, tmp_path):
    cot, mt = _cot(de_tai)
    cot[2].ten = "with"
    with pytest.raises(N.TuChoi, match="từ khoá"):
        N.cu_phap_mau_sav(cot, mt, "x", tmp_path / "m.sav")


# ───────────────────────────── đọc .sav đã nhập ─────────────────────────────


def test_gia_tri_tu_sav_ngay_ma_chu_va_so(de_tai):
    cot, _ = _cot(de_tai)
    theo = {c.ten: c for c in cot}
    nguoc = {-9991.0: "BTR", -9992.0: "KDD"}
    assert N.gia_tri_tu_sav(theo["tuoi"], -9991.0, nguoc, {}) == ("BTR", None, None)
    assert N.gia_tri_tu_sav(theo["tuoi"], 45.0, nguoc, {}) == ("45", None, None)
    assert N.gia_tri_tu_sav(theo["ngay_kham"], _giay(2026, 3, 12), nguoc, {}) == ("2026-03-12", None, None)
    assert N.gia_tri_tu_sav(theo["ngay_kham"], _giay(2026, 3, 12) + 3600, nguoc, {})[1:] == ("ngay_co_gio", N.LOI)
    assert N.gia_tri_tu_sav(theo["ghi_chu"], "  Tốt  ", nguoc, {})[0] == "Tốt"
    assert N.gia_tri_tu_sav(theo["record_id"], 7.0, nguoc, {})[1:] == ("ma_nghien_cuu_luu_dang_so", N.TRUY_VAN)
    assert N.gia_tri_tu_sav(theo["tuoi"], None, nguoc, {}) == ("", None, None)


def _nhap(tmp_path, p: Path, *them) -> int:
    return N.main(["nhap", "--study", STUDY, "--excel", str(p), "--ra", str(tmp_path / "ra"), *them])


def _bao_cao(tmp_path, p: Path) -> dict:
    return json.loads((tmp_path / "ra" / f"{p.stem}_bao_cao_nhap.json").read_text(encoding="utf-8"))


def test_nhap_sav_cung_csv_va_kiem_nhu_excel(de_tai, tmp_path, monkeypatch):
    cot, _ = _cot(de_tai)
    ca = [
        ["P01", 1.0, -9991.0, 1.0, None, _giay(2026, 3, 12), "Tốt"],
        ["P02", 2.0, 130.0, None, 1.0, None, ""],  # tuổi ngoài khoảng ⇒ truy vấn
        [None, None, None, None, None, None, None],  # hàng trống: bỏ qua
    ]
    monkeypatch.setattr(N, "doc_lai_sav", _ban_doc(cot, ca, dac_ta=N.dau_van_tay_dac_ta(cot)))
    p = tmp_path / "lan1.sav"
    p.write_bytes(b"gia")
    assert _nhap(tmp_path, p) == N.MA_LOI
    with open(tmp_path / "ra" / "lan1.csv", encoding="utf-8", newline="") as f:
        doc = list(csv.DictReader(f))
    assert [r["record_id"] for r in doc] == ["P01", "P02"]
    assert doc[0]["tuoi"] == "BTR" and doc[0]["ngay_kham"] == "2026-03-12" and doc[0]["lydo___2"] == "0"
    tv = [(x["ma"], x["o"]) for x in _bao_cao(tmp_path, p)["phat_hien"] if x["muc"] == N.TRUY_VAN]
    assert tv == [("tren_khoang", "ca 2")]


def test_nhap_sav_loi_cau_truc_va_mau_tu_dien_cu(de_tai, tmp_path, monkeypatch):
    cot, _ = _cot(de_tai)
    p = tmp_path / "lan1.sav"
    p.write_bytes(b"gia")
    ca = [["P01", 1.0, 30.0, 0.0, 0.0, None, ""], ["p01", 1.0, 30.0, 0.0, 0.0, None, ""]]
    bien = [c.ten for c in cot] + ["bien_la"]
    monkeypatch.setattr(N, "doc_lai_sav", _ban_doc(cot, [r + [1.0] for r in ca], dac_ta=None, bien=bien))
    assert _nhap(tmp_path, p) == N.MA_LOI and not (tmp_path / "ra" / "lan1.csv").exists()
    assert {"cot_khong_co_trong_tu_dien", "trung_ma_nghien_cuu"} <= {
        x["ma"] for x in _bao_cao(tmp_path, p)["phat_hien"]
    }
    monkeypatch.setattr(N, "doc_lai_sav", _ban_doc(cot, ca[:1], dac_ta="dac-ta-cu"))
    assert _nhap(tmp_path, p) == N.MA_TU_CHOI  # mẫu sinh từ từ điển KHÁC
    assert _nhap(tmp_path, p, "--chap-nhan-tu-dien-moi") == N.MA_OK


def test_so_sanh_nhap_kep_hai_tep_sav(de_tai, tmp_path, monkeypatch):
    cot, _ = _cot(de_tai)
    dac_ta = N.dau_van_tay_dac_ta(cot)
    lan = {
        "lan1": [["P01", 1.0, 40.0, 1.0, 0.0, None, ""]],
        "lan2": [["P01", 1.0, 41.0, 1.0, 0.0, None, ""]],
    }
    monkeypatch.setattr(N, "doc_lai_sav", lambda p: _ban_doc(cot, lan[p.stem], dac_ta=dac_ta)(p))
    for t in lan:
        (tmp_path / f"{t}.sav").write_bytes(b"gia")
    ra = tmp_path / "kep"
    ma = N.main(["so-sanh", "--study", STUDY, "--excel1", str(tmp_path / "lan1.sav"), "--excel2",
                 str(tmp_path / "lan2.sav"), "--ra", str(ra)])  # fmt: skip
    assert ma == N.MA_LOI
    with open(ra / "NHAP_KEP_chi_tiet.csv", encoding="utf-8", newline="") as f:
        lech = list(csv.DictReader(f))
    assert [(x["cot"], x["o_lan1"], x["gia_tri_lan1"], x["gia_tri_lan2"]) for x in lech] == [
        ("tuoi", "SPSS!ca 1", "40", "41")
    ]


# ───────────────────────────── mở trong SPSS / RStudio ─────────────────────────────


def _gia_lap_mo(monkeypatch, d: Path, *, ma_nhap: int = 0, ma_xuat: int = 0, khoa: bool = False):
    goi: list[list[str]] = []
    mo: list[tuple[str, Path]] = []

    def chay(lenh):
        goi.append(lenh)
        cong_cu = Path(lenh[1]).name
        if cong_cu == "nhap_lieu_excel.py" and ma_nhap == 0:
            ra = Path(lenh[lenh.index("--ra") + 1])
            ra.mkdir(parents=True, exist_ok=True)
            ten_csv = Path(lenh[lenh.index("--excel") + 1]).stem + ".csv"
            (ra / ten_csv).write_text("record_id\nP01\n", encoding="utf-8", newline="\n")
            return 0
        if cong_cu in ("cau_noi_spss.py", "cau_noi_r.py"):  # kể cả khi LỖI: tệp CŨ của lượt trước vẫn nằm đó
            hau = "_BAN-NHAP" if "--ban-nhap" in lenh else "_khoa"
            thu, duoi = ("spss", "sav") if cong_cu == "cau_noi_spss.py" else ("r", "rds")
            (d / thu).mkdir(exist_ok=True)
            (d / thu / f"{STUDY}{hau}.{duoi}").write_bytes(b"gia")
            return ma_xuat
        return ma_nhap if cong_cu == "nhap_lieu_excel.py" else ma_xuat

    monkeypatch.setattr(MO, "chay", chay)
    monkeypatch.setattr(MO, "mo_ung_dung", lambda app, tep: mo.append((app, tep)) or True)
    monkeypatch.setattr(MO, "co_du_lieu_khoa", lambda study: khoa)
    return goi, mo


def test_mo_spss_ban_nhap_tu_excel(de_tai, tmp_path, monkeypatch):
    goi, mo = _gia_lap_mo(monkeypatch, de_tai)
    xl = tmp_path / "ngoai" / "lan1.xlsx"
    xl.parent.mkdir()
    xl.write_bytes(b"gia")
    assert MO.main(["spss", "--study", STUDY, "--excel", str(xl)]) == MO.MA_OK
    assert [Path(g[1]).name for g in goi] == ["nhap_lieu_excel.py", "cau_noi_spss.py"]
    assert "--ban-nhap" in goi[1] and goi[1][goi[1].index("--data") + 1].endswith("lan1.csv")
    assert mo == [(MO.APP_SPSS, de_tai / "spss" / f"{STUDY}_BAN-NHAP.sav")]


def test_mo_r_ban_khoa_bo_qua_excel_va_sinh_kich_ban_rstudio(de_tai, tmp_path, monkeypatch):
    goi, mo = _gia_lap_mo(monkeypatch, de_tai, khoa=True)
    assert MO.main(["r", "--study", STUDY, "--excel", str(tmp_path / "lan1.xlsx")]) == MO.MA_OK
    assert [Path(g[1]).name for g in goi] == ["cau_noi_r.py"] and "--ban-nhap" not in goi[0]  # bản KHOÁ
    app, kb = mo[0]
    assert app == MO.APP_RSTUDIO and kb.suffix == ".R"
    noi_dung = kb.read_text(encoding="utf-8")
    assert f"{STUDY}_khoa.rds" in noi_dung and "View(d)" in noi_dung and "ĐÃ KHOÁ" in noi_dung


def test_mo_khong_mo_ban_loi_va_thieu_excel(de_tai, tmp_path, monkeypatch):
    xl = tmp_path / "lan1.xlsx"
    xl.write_bytes(b"gia")
    goi, mo = _gia_lap_mo(monkeypatch, de_tai, ma_nhap=1)
    assert MO.main(["spss", "--study", STUDY, "--excel", str(xl)]) == MO.MA_LOI
    assert [Path(g[1]).name for g in goi] == ["nhap_lieu_excel.py"] and mo == []  # chưa sạch ⇒ không xuất, không mở
    goi, mo = _gia_lap_mo(monkeypatch, de_tai, ma_xuat=1)
    assert MO.main(["spss", "--study", STUDY, "--excel", str(xl)]) == 1 and mo == []  # xuất lỗi ⇒ không mở
    goi, mo = _gia_lap_mo(monkeypatch, de_tai)
    assert MO.main(["r", "--study", STUDY]) == MO.MA_KHONG_DO and goi == [] and mo == []  # chưa khoá, thiếu --excel


# ───────────────────────────── SPSS thật (tự bỏ qua khi không có) ─────────────────────────────


def _co_spss() -> bool:
    try:
        SP.tim_spss()
        return True
    except SP.KhongDoDuoc:
        return False


@pytest.mark.skipif(not _co_spss(), reason="máy không có IBM SPSS Statistics")
def test_mau_sav_that_nhap_lai_khu_hoi(de_tai, tmp_path):
    mau = tmp_path / "mau.sav"
    assert N.main(["mau", "--study", STUDY, "--dang", "sav", "--ra", str(mau)]) == N.MA_OK
    cot, _ = _cot(de_tai)
    nguon = tmp_path / "d.csv"
    nguon.write_text('P01,1,-9991,1,0,12.03.2026,"Phục vụ tốt"\nP02,2,45,0,1,,\n', encoding="utf-8", newline="\n")
    bien = " ".join(f"{c.ten} {N._kieu_spss(c)[1]}" for c in cot)
    sps = tmp_path / "d.sps"
    sps.write_text(
        f"SET UNICODE=ON.\nGET DATA /TYPE=TXT /FILE='{nguon}' /ENCODING='UTF8' /DELIMITERS=\",\" /QUALIFIER='\"'\n"
        f"  /ARRANGEMENT=DELIMITED /FIRSTCASE=1 /VARIABLES={bien}.\nDATASET NAME moi.\n"
        f"ADD FILES /FILE='{mau}' /FILE=moi.\nSAVE OUTFILE='{tmp_path}/lan1.sav'.\n",
        encoding="utf-8",
        newline="\n",
    )
    k = subprocess.run([str(SP.tim_spss()), "-I", str(N.TOOLS / "spss_chay_nen.py"), "--cu-phap", str(sps)],
                       capture_output=True, text=True, check=False)  # fmt: skip
    assert k.returncode == 0, k.stderr
    assert _nhap(tmp_path, tmp_path / "lan1.sav") == N.MA_OK
    with open(tmp_path / "ra" / "lan1.csv", encoding="utf-8", newline="") as f:
        doc = list(csv.DictReader(f))
    assert doc[0]["tuoi"] == "BTR" and doc[0]["ngay_kham"] == "2026-03-12" and doc[0]["ghi_chu"] == "Phục vụ tốt"
    assert doc[1]["tuoi"] == "45" and doc[1]["lydo___2"] == "1" and doc[1]["ngay_kham"] == ""
    shutil.rmtree(tmp_path / "ra")
