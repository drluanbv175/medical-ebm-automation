"""Giá trị cấu trúc bộ câu hỏi (21/11/2026): tools/phan_tich_nhan_to_r.py — EFA nửa 1 + CFA nửa 2 qua R, ĐÚNG phương
pháp SAP đã khoá (C1a, đề cương 4.5.3 ý 4) + tuyến `phan_tich_nhan_to` trong chay_sap_g6.py.

Đọc (chỉ đọc) SAP + từ điển G5 + `_bien-phai-sinh.csv` THẬT của C1a để chứng minh công cụ bám đúng văn bản đã khoá;
mọi dữ liệu là GIẢ LẬP, mọi đầu ra ghi vào tmp_path (không ghi exports/ hay data/). Phần R thật tự bỏ qua khi máy không
có Rscript hoặc thiếu psych/lavaan/GPArotation/jsonlite.
"""

from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
import cau_noi_r as R  # noqa: E402
import cau_noi_spss as S  # noqa: E402
import chay_sap_g6 as CS  # noqa: E402
import phan_tich_nhan_to_r as NT  # noqa: E402

C1A = "hai-long-benh-nhan-C1a-BVQY175"
D_C1A = NT.BASE / "exports" / C1A
SAP_C1A = D_C1A / f"G4_A5_SAP_FINAL_{C1A}.md"
TD_C1A = D_C1A / f"G5_REDCap_dictionary_{C1A}.csv"
CAU_C1A = ([f"a{i}" for i in range(1, 7)] + [f"b{i}" for i in range(1, 9)] + [f"c{i}" for i in range(1, 11)]
           + ["d1", "d2", "d3", "e1", "e2"])  # fmt: skip


def _main(*doi_so: str) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        ma = NT.main(list(doi_so))
    return ma, out.getvalue()


# ───────────────────────── SAP đã khoá ─────────────────────────


def test_sap_c1a_doc_dung_phuong_phap_da_khoa():
    pp = NT.doc_phuong_phap_sap(SAP_C1A)
    assert (pp["so_cau"], pp["linh_vuc"], pp["so_nhan_to"], pp["seed"]) == (29, list("ABCDE"), 5, 20260830)
    assert pp["nguong_sap"] is True
    assert "polychoric" in pp["menh_de"] and "WLSMV" in pp["menh_de"]


@pytest.mark.parametrize(
    "cu, moi, mau",
    [
        ("polychoric", "Pearson", "polychoric"),
        ("WLSMV", "ML", "WLSMV"),
        ("phép xoay xiên", "phép xoay vuông góc", "xoay xiên"),
        ("số nhân tố theo phân tích song song", "số nhân tố theo tiêu chuẩn Kaiser", "phân tích song song"),
        ("phân tầng theo khung giờ và bàn khám", "không phân tầng", "phân tầng"),
        ("phân tích nhân tố khẳng định", "phân tích hồi quy", "khẳng định"),
        ("mô hình năm nhân tố", "mô hình bốn nhân tố", "số nhân tố mô hình"),
        ("set.seed(20260830)", "set.seed(20260830) và set.seed(1)", "ĐÚNG một hạt giống"),
    ],
)
def test_sap_doi_phuong_phap_thi_tu_choi(tmp_path, cu, moi, mau):
    vb = SAP_C1A.read_text(encoding="utf-8")
    assert cu in vb
    p = tmp_path / SAP_C1A.name
    p.write_text(vb.replace(cu, moi), encoding="utf-8", newline="\n")
    with pytest.raises(NT.TuChoi, match=mau):
        NT.doc_phuong_phap_sap(p)


def test_sap_doi_nguong_thi_chi_in_so(tmp_path):
    p = tmp_path / SAP_C1A.name
    p.write_text(SAP_C1A.read_text(encoding="utf-8").replace("RMSEA ≤ 0,06", "RMSEA ≤ 0,07"), encoding="utf-8",
                 newline="\n")  # fmt: skip
    assert NT.doc_phuong_phap_sap(p)["nguong_sap"] is False


def test_sap_vang_la_khong_do_duoc(tmp_path):
    with pytest.raises(NT.KhongDoDuoc):
        NT.doc_phuong_phap_sap(tmp_path / "khong_co.md")


# ───────────────────────── từ điển G5 ─────────────────────────


def test_cau_theo_linh_vuc_c1a_tu_tieu_de_phan():
    lv = NT.cau_theo_linh_vuc(TD_C1A, list("ABCDE"))
    assert {k: len(v) for k, v in lv.items()} == {"A": 6, "B": 8, "C": 10, "D": 3, "E": 2}
    assert [c for k in "ABCDE" for c in lv[k]] == CAU_C1A  # f1 (lĩnh vực F) và trường HIS không lọt vào


def test_thang_hop_le_ma_sau_khoang_trong_la_thieu():
    td = S.doc_tu_dien(TD_C1A)
    assert NT.thang_hop_le(td["a1"]) == [1, 2, 3, 4, 5]  # 8, 9 là mã thiếu
    assert NT.thang_hop_le({"loai": "radio", "lua_chon": "0, x | 1, y | 2, z | 9, kb"}) == [0, 1, 2]


def test_kiem_pii_cot():
    td = S.doc_tu_dien(TD_C1A)
    NT.kiem_pii_cot(td, ["khunggio_kham", "ma_ban_kham", *CAU_C1A])
    with pytest.raises(NT.TuChoi, match="ĐỊNH DANH"):  # từ điển C1a không có trường Identifier=y ⇒ dựng giả
        NT.kiem_pii_cot({**td, "ho_ten": {"dinh_danh": "y"}}, ["ho_ten", "a1"])
    with pytest.raises(NT.TuChoi, match="không có trong từ điển"):
        NT.kiem_pii_cot(td, ["cot_la", "a1"])


# ───────────────────────── phân loại · chia nửa · cảnh báo thiếu ─────────────────────────


@pytest.mark.parametrize(
    "cfi, tli, rmsea, srmr, ket",
    [
        (0.95, 0.95, 0.06, 0.08, "tot"),  # đúng biên ⇒ đạt (≥, ≤)
        (0.95, 0.95, 0.061, 0.08, "chap_nhan_duoc"),
        (0.96, 0.96, 0.05, 0.081, "chap_nhan_duoc"),  # SRMR chỉ thuộc mức «tốt»
        (0.90, 0.90, 0.08, 0.20, "chap_nhan_duoc"),
        (0.899, 0.95, 0.05, 0.05, "khong_dat"),
        (0.95, 0.95, 0.081, 0.05, "khong_dat"),
        (None, 0.95, 0.05, 0.05, "khong_du_chi_so"),
    ],
)
def test_phan_loai_theo_nguong_dinh_truoc(cfi, tli, rmsea, srmr, ket):
    cs = {"cfi.scaled": cfi, "tli.scaled": tli, "rmsea.scaled": rmsea, "srmr": srmr}
    assert NT.phan_loai(cs, "scaled") == ket


def _tap_chia(tmp_path: Path, nua: list[str], tang: list[str]) -> tuple[Path, Path]:
    dl, ch = tmp_path / "dl.csv", tmp_path / "chia.csv"
    NT.ghi_csv(dl, ["dong", "t"], [[i + 1, t] for i, t in enumerate(tang)])
    NT.ghi_csv(ch, ["dong", "nua"], [[f'"{i + 1}"', n] for i, n in enumerate(nua)])
    return dl, ch


@pytest.mark.parametrize(
    "nua, tang, loi",
    [
        (["1", "2", "1", "2", "1"], ["a", "a", "b", "b", "c"], None),
        (["1", "1", "1", "2"], ["a", "a", "a", "a"], "lệch 2"),
        (["1", "0", "2"], ["a", "a", "b"], "không thuộc nửa nào"),
    ],
)
def test_kiem_chia_nua(tmp_path, nua, tang, loi):
    dl, ch = _tap_chia(tmp_path, nua, tang)
    kq = NT.kiem_chia_nua(dl, ch, ["t"])
    if loi is None:
        assert kq["loi"] == [] and kq["lech_toi_da_trong_tang"] <= 1 and kq["so_tang"] == 3
    else:
        assert any(loi in x for x in kq["loi"]), kq


def test_canh_bao_listwise_theo_luat_5_phan_tram_cua_sap():
    cb = NT.canh_bao_listwise("listwise", {"n": 95, "n_nua": 100}, {"n": 96, "n_nua": 100})  # 5% ⇒ có; 4% ⇒ không
    assert len(cb) == 1 and cb[0].startswith("Nửa 1") and "5,0%" in cb[0] and "SAP §6" in cb[0]
    assert NT.canh_bao_listwise("pairwise", {"n": 10, "n_nua": 100}, {}) == []


def _ngu_canh_gia(tmp_path: Path, kq_r: dict, nguong: bool = True) -> dict:
    dl, ch = _tap_chia(tmp_path, ["1", "2"], ["a", "a"])
    p = tmp_path / "kq.json"
    p.write_text(json.dumps(kq_r), encoding="utf-8", newline="\n")
    dac = {"sap": {"tep_sap": "SAP.md", "sha256_sap": "0" * 64, "menh_de": "m", "seed": 7, "nguong_sap": nguong},
           "seed": 7, "cau": ["a1"], "nhom": ["A"], "tang": ["t"], "thieu": "pairwise",
           "thong_ke_tap": {"n_ban_dau": 2, "n_sau_loc": 2, "ma_ngoai_thang": {}, "dong_thieu_tang": 0}}
    return {"dac": dac, "tep_kq": p, "tep_chia": ch, "tep_dl": dl}


CS_TOT = {"cfi": 1, "tli": 1, "rmsea": 0, "srmr": 0.03, "cfi.scaled": 0.99, "tli.scaled": 0.99, "rmsea.scaled": 0.02,
          "cfi.robust": 0.97, "tli.robust": 0.97, "rmsea.robust": 0.07}


@pytest.mark.parametrize(
    "cfa, loi, ma, phan_scaled",
    [
        ({"hoi_tu": True, "nghiem_hop_le": True, "chi_so": CS_TOT}, {}, 0, "tot"),
        ({"hoi_tu": False, "nghiem_hop_le": False, "chi_so": CS_TOT}, {}, 1, "khong_phan_loai_khong_hoi_tu"),
        ({"hoi_tu": True, "nghiem_hop_le": False, "chi_so": CS_TOT}, {}, 0, "khong_phan_loai_nghiem_khong_hop_le"),
        ({"hoi_tu": True, "nghiem_hop_le": True, "chi_so": CS_TOT}, {"efa": "lỗi"}, 1, "tot"),
    ],
)
def test_doc_ket_qua_r_ma_thoat_va_phan_loai(tmp_path, cfa, loi, ma, phan_scaled):
    c = _ngu_canh_gia(tmp_path, {"efa": {"n": 1, "n_nua": 1}, "cfa": cfa, "loi": loi})
    nt, m = NT.doc_ket_qua_r(c, 0, "", "", chay_bang="giả")
    assert m == ma and nt["phan_loai_theo_nguong_dinh_truoc"]["scaled"] == phan_scaled
    assert nt["phan_loai_theo_nguong_dinh_truoc"]["robust"] in ("chap_nhan_duoc", phan_scaled)


def test_doc_ket_qua_r_khong_nguong_thi_khong_phan_loai(tmp_path):
    c = _ngu_canh_gia(tmp_path, {"efa": {"n": 1}, "cfa": {"hoi_tu": True, "nghiem_hop_le": True, "chi_so": CS_TOT}},
                      nguong=False)  # fmt: skip
    nt, _m = NT.doc_ket_qua_r(c, 0, "", "", chay_bang="giả")
    assert nt["phan_loai_theo_nguong_dinh_truoc"] is None and nt["nguon_nguong"] is None


def test_doc_ket_qua_r_r_sap_khong_ghi_json(tmp_path):
    c = _ngu_canh_gia(tmp_path, {})
    c["tep_kq"].unlink()
    nt, m = NT.doc_ket_qua_r(c, 1, "", "Error in x", chay_bang="giả")
    assert m == 1 and "Error in x" in nt["loi"]["r"]


# ───────────────────────── script R ─────────────────────────


def test_script_hien_thuc_dung_phuong_phap_sap():
    pp = NT.doc_phuong_phap_sap(SAP_C1A)
    tang = ["khunggio_kham", "x@@SEED@@"]
    vb = NT.sinh_script(C1A, pp, pp["seed"], Path("/t/dl.csv"), "AB" * 32, Path("/t/kq.json"), Path("/t/c.csv"),
                        CAU_C1A, list("A" * 6 + "B" * 8 + "C" * 10 + "D" * 3 + "E" * 2), tang, "listwise")
    ma = "\n".join(d for d in vb.splitlines() if not d.strip().startswith("#"))
    assert "SEED     <- 20260830L" in ma and ma.count("set.seed(SEED)") == 3
    # thứ tự tầng theo MÃ KÝ TỰ (radix), không theo locale — chia nửa giống nhau trên Mac lẫn Windows
    assert 'cac_tang <- sort(unique(khoa), method = "radix")' in ma
    assert "options(mc.cores = 1L)" in ma  # psych song song + Mersenne-Twister ⇒ hạt giống không tái lập được
    assert ma.count('cor = "poly"') == 2 and "psych::fa.parallel(" in ma and "sim = FALSE" in ma
    assert '"oblimin"' in ma and 'estimator = "WLSMV"' in ma and "ordered = CAU" in ma
    assert "modindices" not in ma.lower() and "modificationindices" not in ma.lower()
    assert '"x@@SEED@@"' in ma  # thay MỘT lượt: tên cột không kéo được mã khác vào script
    assert all(ord(ch) < 128 for ch in ma), "chuỗi R phải ASCII (locale C)"


# ───────────────────────── giả lập ─────────────────────────


def test_gia_lap_tat_dinh_va_rao_ghi(tmp_path):
    t1, d1 = NT.sinh_gia_lap(200, 5, "nam_nhan_to")
    t2, d2 = NT.sinh_gia_lap(200, 5, "nam_nhan_to")
    assert (t1, d1) == (t2, d2) and t1[:2] == ["khunggio_kham", "ma_ban_kham"] and t1[2:31] == CAU_C1A
    assert "record_id" not in t1
    assert any(sum(1 for x in h[2:31] if x == "9") >= 7 for h in d1)  # có phiếu bị PhieuHopLe loại
    assert NT.sinh_gia_lap(200, 5, "khong_cau_truc")[1] != d1
    with pytest.raises(NT.TuChoi):
        NT.sinh_gia_lap(10, 5, "la")
    assert _main("gia-lap", "--ra", str(NT.BASE / "data" / "x.csv"))[0] == 3
    ra = tmp_path / "gl.csv"
    assert _main("gia-lap", "--ra", str(ra), "--n", "50")[0] == 0 and ra.is_file()
    assert _main("gia-lap", "--ra", str(ra), "--n", "50")[0] == 3  # không ghi đè khi thiếu --ghi-de


# ───────────────────────── chuẩn bị tập phân tích (bản nháp, C1a thật chỉ đọc) ─────────────────────────


def _csv_nho(p: Path) -> None:
    tieu_de = ["khunggio_kham", "ma_ban_kham", *CAU_C1A, "f1", "g1"]
    dong = []
    for i in range(12):
        o = [str(1 + (i + j) % 5) for j in range(29)]
        dong.append([str(1 + i % 4), f"BK{1 + i % 3:02d}", *o, "4", "4"])
    dong[0][2], dong[1][3], dong[2][4], dong[3][5] = "8", "9", "KDD", ""
    dong[11][-1] = ""  # thiếu G1 ⇒ PhieuHopLe = 0
    NT.ghi_csv(p, tieu_de, dong)


@pytest.fixture
def c1a_ban_chep_duyet_thu(tmp_path, monkeypatch):
    """Bản chép TẠM thư mục C1a cho test logic: công thức biến phái sinh đã đổi (dấu duyệt thật HẾT HIỆU LỰC, chờ thống
    kê viên ký trong gói ký) được đóng dấu KIỂM THỬ trên bản chép — test đo logic chuẩn bị tập/cú pháp, không phụ
    thuộc trạng thái chữ ký đời thực của đề tài (22/11/2026: hội đồng đổi công thức PhieuHopLe ⇒ 3 test kín đỏ). Tệp
    thật không đổi."""
    import bien_phai_sinh as BPS  # noqa: PLC0415

    goc = tmp_path / "exports_thu"
    dich = goc / C1A
    dich.mkdir(parents=True)
    for f in D_C1A.iterdir():
        if f.is_file() and f.suffix in (".csv", ".md", ".json"):
            shutil.copy2(f, dich / f.name)
    p = dich / "_bien-phai-sinh.csv"
    with open(p, encoding="utf-8", newline="") as fh:
        doc = csv.DictReader(fh)
        cot, dong = doc.fieldnames, list(doc)
    for r in dong:
        dau = BPS.dau_cong_thuc(r["ten_bien"], r["cong_thuc"], r.get("lap_k") or "")
        if BPS.trang_thai_duyet(r.get("nguoi_duyet") or "", dau) == "HET_HIEU_LUC":
            r["nguoi_duyet"] = f"KIEM-THU:fixture-tam:2026-11-22:{dau}"
    with open(p, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cot)
        w.writeheader()
        w.writerows(dong)
    monkeypatch.setattr(S, "EXPORTS", goc)
    return dich


def test_chuan_bi_tap_dem_ma_ngoai_thang_va_loc_quan_the(tmp_path, c1a_ban_chep_duyet_thu):
    pytest.importorskip("pandas")
    p = tmp_path / "x.csv"
    _csv_nho(p)
    td = S.doc_tu_dien(TD_C1A)
    dong, tk = NT.chuan_bi_tap(C1A, p, CAU_C1A, ["khunggio_kham", "ma_ban_kham"], "PhieuHopLe == 1",
                               {c: NT.thang_hop_le(td[c]) for c in CAU_C1A})  # fmt: skip
    assert (tk["n_ban_dau"], tk["n_sau_loc"]) == (12, 11)
    assert tk["ma_ngoai_thang"] == {"(trống)": 1, "8": 1, "9": 1, "KDD": 1}
    assert len(dong) == 11 and dong[0][3] == "" and dong[0][4] != ""


def _cu_phap_nhap(tmp_path: Path, *them: str) -> tuple[int, str]:
    p = tmp_path / "x.csv"
    _csv_nho(p)
    return _main("cu-phap", "--study", C1A, "--data", str(p), "--ban-nhap", "--thu-muc-ra", str(tmp_path / "ra"),
                 "--tang", "khunggio_kham,ma_ban_kham", "--loc", "PhieuHopLe == 1", *them)


def test_cu_phap_ban_nhap_ghi_ngoai_repo_dung_seed_sap(tmp_path, c1a_ban_chep_duyet_thu):
    pytest.importorskip("pandas")
    truoc = sorted((x.name, x.stat().st_mtime_ns) for x in D_C1A.iterdir())
    ma, ra = _cu_phap_nhap(tmp_path)
    assert ma == 0, ra
    assert sorted((x.name, x.stat().st_mtime_ns) for x in D_C1A.iterdir()) == truoc  # exports/ thật không đổi
    dac = json.loads((tmp_path / "ra" / "nhan_to_dac_ta.json").read_text(encoding="utf-8"))
    assert dac["seed"] == 20260830 and dac["ban_nhap"] is True and dac["cau"] == CAU_C1A
    assert any("BẢN NHÁP" in x for x in dac["canh_bao"])
    with open(tmp_path / "ra" / "nhan_to_du_lieu.csv", encoding="utf-8") as f:
        assert next(csv.reader(f)) == ["dong", "khunggio_kham", "ma_ban_kham", *CAU_C1A]
    assert dac["sha256_tap"] == hashlib.sha256((tmp_path / "ra" / "nhan_to_du_lieu.csv").read_bytes()).hexdigest()
    assert (tmp_path / "ra" / f"{C1A}_nhan_to.R").is_file()


def test_cu_phap_seed_khac_sap_ghi_ro(tmp_path, c1a_ban_chep_duyet_thu):
    pytest.importorskip("pandas")
    ma, ra = _cu_phap_nhap(tmp_path, "--seed", "1")
    assert ma == 0 and "KHÁC SAP" in ra


@pytest.mark.parametrize(
    "doi_so, mau",
    [
        (["--data", "x.csv"], "--ban-nhap"),
        (["--data", "x.csv", "--ban-nhap"], "--thu-muc-ra"),
        (["--data", "x.csv", "--ban-nhap", "--thu-muc-ra", str(NT.BASE / "exports" / "z")], "NGOÀI repo"),
        (["--ban-nhap"], "chỉ dùng kèm --data"),
    ],
)
def test_rao_ban_nhap(doi_so, mau):
    ma, ra = _main("cu-phap", "--study", C1A, "--tang", "khunggio_kham", *doi_so)
    assert ma == 3 and mau in ra


def test_tu_dien_lech_so_cau_sap_thi_tu_choi(tmp_path):
    pytest.importorskip("pandas")
    td = tmp_path / "td.csv"
    with open(TD_C1A, encoding="utf-8-sig", newline="") as f, open(td, "w", encoding="utf-8", newline="") as g:
        w = csv.writer(g)
        for r in csv.reader(f):
            if r[0] != "e2":
                w.writerow(r)
    ma, ra = _cu_phap_nhap(tmp_path, "--dictionary", str(td))
    assert ma == 3 and "SAP ghi 29 câu" in ra


def test_che_do_khoa_doi_g4_va_du_lieu_khoa(monkeypatch):
    import run_stats_analysis as RSA

    monkeypatch.setattr(RSA, "_g4_khoa_song", lambda s: (False, "chưa ký"))
    ma, ra = _main("cu-phap", "--study", C1A, "--tang", "khunggio_kham")
    assert ma == 3 and "G4" in ra
    monkeypatch.setattr(RSA, "_g4_khoa_song", lambda s: (True, "giả"))

    def chua_khoa(_s):
        raise NT.KhongDoDuoc("chưa có manifest khoá dữ liệu")

    monkeypatch.setattr(S, "tim_du_lieu_khoa", chua_khoa)
    assert _main("cu-phap", "--study", C1A, "--tang", "khunggio_kham")[0] == 2


def test_khong_co_r_ma_2_van_sinh_script(tmp_path, monkeypatch):
    pytest.importorskip("pandas")

    def khong_r():
        raise NT.KhongDoDuoc("không tìm thấy Rscript")

    monkeypatch.setattr(R, "tim_r", khong_r)
    p = tmp_path / "x.csv"
    _csv_nho(p)
    ma, ra = _main("chay", "--study", C1A, "--data", str(p), "--ban-nhap", "--thu-muc-ra", str(tmp_path / "ra"),
                   "--tang", "khunggio_kham,ma_ban_kham")  # fmt: skip
    assert ma == 2 and (tmp_path / "ra" / f"{C1A}_nhan_to.R").is_file()


# ───────────────────────── tuyến chay_sap_g6 ─────────────────────────

TS_NT = {"phan_tich_nhan_to": "efa_cfa", "tang": ["khunggio_kham", "ma_ban_kham"], "loc": "PhieuHopLe == 1"}


def _de_tai_g6(goc: Path, ts_nt: dict) -> Path:
    d = goc / "exports" / "NT"
    d.mkdir(parents=True)
    sap = d / "G4_A5_SAP_FINAL_NT.md"
    sap.write_text("# SAP\n§4\n", encoding="utf-8", newline="\n")
    dt = {"nguon_sap": sap.name, "sha256_sap": hashlib.sha256(sap.read_bytes()).hexdigest(), "phan_tich": [
        {"id": "chinh", "vai": "chinh", "sap_muc": "§4", "mo_ta": "thứ tự", "tham_so": {"outcome": "g1"}},
        {"id": "MO_nhan_to", "vai": "mo_ta", "sap_muc": "§3", "mo_ta": "giá trị cấu trúc", "tham_so": ts_nt}]}
    dt["nguoi_duyet"] = f"THONG_KE_VIEN:T:2026-11-21:{CS.dau_dac_ta(dt)}"
    (d / CS.TEP_DAC_TA).write_text(json.dumps(dt, ensure_ascii=False), encoding="utf-8", newline="\n")
    return d


def test_g6_dac_ta_nhan_to_hop_le_va_doi_so(tmp_path):
    d = _de_tai_g6(tmp_path, dict(TS_NT))
    assert CS.kiem_dac_ta(d, CS.doc_dac_ta(d))["loi"] == []
    assert CS.doi_so_run_stats({"tham_so": dict(TS_NT, thieu="pairwise")}) == [
        "--phan-tich-nhan-to", "efa_cfa", "--tang", "khunggio_kham,ma_ban_kham", "--loc", "PhieuHopLe == 1",
        "--thieu", "pairwise"]  # fmt: skip


@pytest.mark.parametrize(
    "ts, mau",
    [
        ({"phan_tich_nhan_to": "efa_cfa"}, "thiếu tang"),
        ({**TS_NT, "outcome": "g1"}, "không áp dụng cho phân tích nhân tố: outcome"),
        ({"outcome": "g1", "tang": ["a"]}, "chỉ dùng kèm phan_tich_nhan_to"),
        ({**TS_NT, "phan_tich_nhan_to": "pca"}, "phải thuộc"),
        ({**TS_NT, "thieu": "mean"}, "listwise hoặc pairwise"),
        ({**TS_NT, "tang": ["-x"]}, "danh sách tên"),
    ],
)
def test_g6_dac_ta_nhan_to_sai_bi_bat(tmp_path, ts, mau):
    d = _de_tai_g6(tmp_path, ts)
    loi = CS.kiem_dac_ta(d, CS.doc_dac_ta(d))["loi"]
    assert any(mau in x for x in loi), loi


def test_g6_dinh_tuyen_sang_cong_cu_nhan_to(tmp_path, monkeypatch):
    d = _de_tai_g6(tmp_path, dict(TS_NT))
    monkeypatch.setattr(CS, "BASE", tmp_path)
    monkeypatch.setattr(S, "tim_du_lieu_khoa", lambda s: (d / "k.csv", {}))
    (d / "k.csv").write_text("g1\n1\n", encoding="utf-8", newline="\n")
    goi: list[list[str]] = []

    def chay_gia(lenh, **kw):
        goi.append(lenh)
        gate = lenh[lenh.index("--gate") + 1]
        tom = {"n_total": 9}
        if "phan_tich_nhan_to_r.py" in lenh[1]:
            tom["nhan_to"] = {"efa": {"song_song": {"so_nhan_to": 4}},
                              "cfa": {"hoi_tu": True, "chi_so": {"cfi.scaled": 0.97, "srmr": 0.05}},
                              "phan_loai_theo_nguong_dinh_truoc": {"scaled": "tot"}}
        (d / f"{gate}_analysis_summary.json").write_text(json.dumps(tom), encoding="utf-8", newline="\n")
        return subprocess.CompletedProcess(lenh, 0, "", "")

    monkeypatch.setattr(CS.subprocess, "run", chay_gia)
    with contextlib.redirect_stdout(io.StringIO()):
        assert CS.main(["chay", "--study", "NT", "--kiem-cheo"]) == 0
    lenh_nt = next(x for x in goi if "phan_tich_nhan_to_r.py" in x[1])
    assert lenh_nt[2:6] == ["chay", "--study", "NT", "--gate"] and lenh_nt[6] == "G6_MO_nhan_to"
    assert "--data" not in lenh_nt and "--kiem-cheo" not in lenh_nt  # tự đọc bộ khoá; không có kiểm chéo SPSS
    assert not [x for lenh in goi for x in lenh if x.startswith("--i-confirm")]
    cm = json.loads((d / CS.TEP_KQ_JSON).read_text(encoding="utf-8"))
    ul = next(x for x in cm["phan_tich"] if x["id"] == "MO_nhan_to")["uoc_luong"]["nhan_to"]
    assert ul["so_nhan_to_song_song"] == 4 and ul["cfi_scaled"] == 0.97 and ul["phan_loai"] == {"scaled": "tot"}


# ───────────────────────── R THẬT (bỏ qua khi máy không có R/gói) ─────────────────────────


def _co_r() -> bool:
    try:
        return not NT.kiem_goi(R.tim_r())["thieu"]
    except Exception:  # noqa: BLE001
        return False


CO_R = shutil.which("Rscript") is not None and _co_r()
can_r = pytest.mark.skipif(not CO_R, reason="máy không có Rscript hoặc thiếu psych/lavaan/GPArotation/jsonlite")


def _chay_gia_lap(tmp_path: Path, kich_ban: str, ten: str, n: int = 600) -> tuple[int, dict, Path]:
    p = tmp_path / f"{kich_ban}.csv"
    if not p.exists():
        assert _main("gia-lap", "--ra", str(p), "--n", str(n), "--kich-ban", kich_ban)[0] == 0
    ra = tmp_path / ten
    ma, out = _main("chay", "--study", C1A, "--data", str(p), "--ban-nhap", "--thu-muc-ra", str(ra), "--tang",
                    "khunggio_kham,ma_ban_kham", "--loc", "PhieuHopLe == 1", "--thieu", "pairwise")  # fmt: skip
    tom = json.loads((ra / f"{NT.GATE_MAC_DINH}_analysis_summary.json").read_text(encoding="utf-8"))
    return ma, tom, ra


@can_r
def test_r_that_nam_nhan_to_tai_lap_va_dung_uoc_luong(tmp_path, c1a_ban_chep_duyet_thu):
    pytest.importorskip("pandas")
    ma, tom, ra = _chay_gia_lap(tmp_path, "nam_nhan_to", "l1")
    assert ma == 0, tom["nhan_to"]["loi"]
    nt = tom["nhan_to"]
    assert tom["ban_nhap"] is True and "data_lock" not in tom  # G7 không dựng Kết quả từ bản nháp
    cn = nt["chia_nua"]
    assert cn["kiem_python"]["loi"] == [] and cn["kiem_python"]["lech_toi_da_trong_tang"] <= 1
    assert cn["n_nua_1"] + cn["n_nua_2"] == tom["n_total"]
    ss = nt["efa"]["song_song"]
    assert ss["so_nhan_to"] >= 3 and nt["efa"]["fa"]["so_nhan_to"] == ss["so_nhan_to"]
    assert isinstance(ss.get("so_nhan_to_pv95"), int) and ss["so_nhan_to_pv95"] <= ss["so_nhan_to"]  # 95% chặt hơn
    assert all(p >= t for p, t in zip(ss["tri_rieng_pv95"], ss["tri_rieng_tai_chon"]))
    cfa = nt["cfa"]
    assert cfa["hoi_tu"] and cfa["uoc_luong"]["estimator"] == "DWLS" and "scaled" in cfa["uoc_luong"]["test"]
    assert cfa["uoc_luong"]["bien_thu_bac"] == CAU_C1A
    assert set(nt["phan_loai_theo_nguong_dinh_truoc"]) == {"thuong", "scaled", "robust"}
    md = (ra / f"{NT.GATE_MAC_DINH}_ket_qua.md").read_text(encoding="utf-8")
    assert "[CẦN THỐNG KÊ VIÊN XÁC NHẬN]" in md and "BẢN NHÁP" in md and "PMID 29869222" in md
    ma2, tom2, ra2 = _chay_gia_lap(tmp_path, "nam_nhan_to", "l2")
    assert ma2 == 0
    assert (ra / "nhan_to_chia_nua.csv").read_bytes() == (ra2 / "nhan_to_chia_nua.csv").read_bytes()
    assert tom2["nhan_to"]["cfa"]["chi_so"] == cfa["chi_so"]
    # cùng hạt giống ⇒ CẢ phân tích song song (bước dùng số ngẫu nhiên sau chia nửa) phải trùng khớp từng chữ số
    assert tom2["nhan_to"]["efa"]["song_song"] == ss and tom2["nhan_to"]["efa"]["fa"] == nt["efa"]["fa"]


@can_r
def test_r_that_du_lieu_nhieu_khong_trich_thua_khong_phan_loai_dat(tmp_path, c1a_ban_chep_duyet_thu):
    pytest.importorskip("pandas")
    ma, tom, _ra = _chay_gia_lap(tmp_path, "khong_cau_truc", "n1", n=1000)
    nt = tom["nhan_to"]
    ss = nt["efa"]["song_song"]
    # Mốc hồi quy ĐO 21/11/2026 trên đúng bộ nhiễu có hạt giống này (nửa 1: 497 phiếu): sim = FALSE ⇒ 0, mặc định psych
    # sim = TRUE ⇒ 5. KHÔNG phải khẳng định phân tích song song không bao giờ ra nhân tố giả: bộ nhiễu n 600 (nửa 1:
    # 298) vẫn ra 3 theo cả tiêu chí trung bình lẫn phân vị 95% — vì vậy báo cáo đọc kèm hệ số tải và CFA nửa 2.
    assert ss["so_nhan_to"] <= 2 and ss["so_nhan_to_pv95"] <= ss["so_nhan_to"]
    pl = nt["phan_loai_theo_nguong_dinh_truoc"] or {}
    assert pl.get("scaled") not in ("tot", "chap_nhan_duoc"), pl  # CFI/RMSEA nhiễu trông «hoàn hảo» — post.check chặn
    assert ma in (0, 1)
