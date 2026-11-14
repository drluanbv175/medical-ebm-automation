"""Kiểm cầu nối R (tools/cau_noi_r.py) — 14/11/2026.

Không cần R: tệp mẫu trong tests/fixtures/r_ket_qua/ là đầu ra THẬT của R 4.6.2 (script do `cu-phap` sinh, chạy trên
dữ liệu giả 400 ca) cùng tóm tắt G6 của chính run_stats_analysis.py trên cùng dữ liệu (đã gỡ đường dẫn máy). Một test
chạy R thật (đi trọn run_stats_analysis.py → cu-phap → chay → doi-chieu), tự bỏ qua khi máy không có Rscript.
Chốt khớp chuỗi trên script R chỉ khớp DÒNG THI HÀNH (đã bỏ chú thích) — CLAUDE.md §0.8.
"""

from __future__ import annotations

import contextlib
import copy
import csv
import hashlib
import io
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import cau_noi_r as R  # noqa: E402
import cau_noi_spss as S  # noqa: E402

FX = Path(__file__).resolve().parent / "fixtures" / "r_ket_qua"


def _fx(ten: str) -> tuple[dict, dict]:
    return (
        json.loads((FX / f"{ten}_python.json").read_text(encoding="utf-8")),
        json.loads((FX / f"{ten}_r.json").read_text(encoding="utf-8")),
    )


def _dong_thi_hanh(vb: str) -> list[str]:
    """Các dòng R THỰC THI: bỏ dòng chú thích và phần chú thích cuối dòng (không nằm trong chuỗi)."""
    ra = []
    for d in vb.splitlines():
        s = d.strip()
        if not s or s.startswith("#"):
            continue
        ngoai, trong = [], None
        for ch in d:
            if trong:
                if ch == trong:
                    trong = None
            elif ch in "\"'":
                trong = ch
            elif ch == "#":
                break
            ngoai.append(ch)
        ra.append("".join(ngoai).strip())
    return ra


# ───────────── tiện ích chuỗi R / tìm Rscript ─────────────


def test_chuoi_r_thoat_dung_va_ascii():
    assert R.chuoi_r('a"b\\c') == '"a\\"b\\\\c"'
    assert R.chuoi_r("tuổi") == '"tu\\u1ed5i"'  # ASCII thuần — R đọc đúng ở mọi mã trang
    assert R.vec_r([]) == "character(0)" and R.vec_r(["a", "b"]) == 'c("a", "b")'
    assert R.gia_tri_r(None) == "NA_character_" and R.gia_tri_r(None, so=True) == "NA_real_"
    assert R.gia_tri_r(15, so=True) == "15.0"


def test_ung_vien_rscript_windows_chon_ban_moi_nhat(tmp_path, monkeypatch):
    monkeypatch.delenv("EBM_RSCRIPT", raising=False)
    monkeypatch.setattr(R.shutil, "which", lambda _t: None)
    goc = tmp_path / "R"
    for ban in ("R-4.4.1", "R-4.10.0", "R-4.6.2"):
        (goc / ban / "bin").mkdir(parents=True)
        (goc / ban / "bin" / "Rscript.exe").write_text("", encoding="utf-8", newline="\n")
    ds = R.ung_vien_rscript(he="nt", goc_cai=[goc])
    assert [p.parent.parent.name for p in ds] == ["R-4.10.0", "R-4.6.2", "R-4.4.1"]  # so số, không so chữ
    monkeypatch.setenv("EBM_RSCRIPT", "/khac/Rscript")
    assert R.ung_vien_rscript(he="nt", goc_cai=[goc]) == [Path("/khac/Rscript")]


def test_kiem_khong_co_r_la_khong_do_duoc(monkeypatch):
    monkeypatch.setattr(R, "ung_vien_rscript", lambda *a, **k: [])
    assert R.main(["kiem"]) == R.MA_KHONG_DO


def test_cai_goi_mac_dinh_chay_kho_khong_cai(monkeypatch):
    monkeypatch.setattr(R, "tim_r", lambda: Path("Rscript"))
    monkeypatch.setattr(R, "kiem_moi_truong", lambda _r: {"ma": 0, "thieu": ["ordinal"], "goi": {}})
    goi = []
    monkeypatch.setattr(R, "chay_r", lambda *a, **k: goi.append(a) or (0, "", ""))
    assert R.main(["cai-goi"]) == R.MA_LECH and not goi  # chạy khô: không gọi R để cài


# ───────────── đề tài giả + cu-phap ─────────────

CSV_MAU = (
    "record_id,nhom,tuoi,gioitinh,nghe,ban,kq,thoi_gian,bien_co\n"
    "P1,0,50.5,1,khac,1,0,30,1\nP2,1,,2,BTR,2,1,45,0\nP3,1,61,1,cong_chuc,1,1,20,1\nP4,0,NA,2,khac,2,0,60,0\n"
)


def _de_tai(tmp_path: Path, monkeypatch, *, dinh_danh: str = "", tom: dict | None = None) -> Path:
    monkeypatch.setattr(S, "EXPORTS", tmp_path / "exports")
    d = tmp_path / "exports" / "THU"
    (d / "05_clean_locked").mkdir(parents=True)
    k = d / "05_clean_locked" / "k.csv"
    k.write_text(CSV_MAU, encoding="utf-8", newline="")
    (d / "DATA_LOCK_manifest.json").write_text(
        json.dumps(
            {
                "locked_dataset_path": "05_clean_locked/k.csv",
                "sha256": hashlib.sha256(k.read_bytes()).hexdigest(),
                "lock_date": "2026-11-14",
            }
        ),
        encoding="utf-8",
        newline="\n",
    )
    with open(d / "G5_REDCap_dictionary_THU.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Variable / Field Name", "Field Type", "Field Label", "Identifier?"])
        for c in CSV_MAU.splitlines()[0].split(","):
            w.writerow([c, "text", c, dinh_danh if c == "record_id" else ""])
    (d / "_ma-thieu-theo-bien.csv").write_text("bien,ma,nhan\n*,BTR,Bỏ trống\n", encoding="utf-8", newline="\n")
    tom = (
        tom
        if tom is not None
        else {
            "dac_ta_phan_tich": {
                "outcome": "kq",
                "group": "nhom",
                "covariates": ["tuoi", "gioitinh"],
                "outcome_type": "auto",
                "time": "thoi_gian",
                "event": "bien_co",
                "cot_cum": "ban",
            },
            "primary_outcome": {"outcome_type": "binary"},
        }
    )
    (d / "G6_analysis_summary.json").write_text(json.dumps(tom), encoding="utf-8", newline="\n")
    return d


def _cu_phap(*them: str) -> int:
    with contextlib.redirect_stdout(io.StringIO()):
        return R.main(["cu-phap", "--study", "THU", *them])


def test_cu_phap_sinh_script_dung_dac_ta_g6(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch)
    assert _cu_phap() == R.MA_OK
    vb = (d / "r" / "THU_phan_tich.R").read_text(encoding="utf-8")
    th = _dong_thi_hanh(vb)
    sha = json.loads((d / "DATA_LOCK_manifest.json").read_text(encoding="utf-8"))["sha256"]
    for dong in (
        'KET_CUC <- "kq"',
        'NHOM <- "nhom"',
        'HIEP_BIEN <- c("tuoi", "gioitinh")',
        'LOAI_KET_CUC <- "binary"',
        'THOI_GIAN <- "thoi_gian"',
        'BIEN_CO <- "bien_co"',
        'CUM <- "ban"',
        f'SHA256_KHOA <- "{sha}"',
        "DON_VI_PHOI_NHIEM <- NA_real_",
    ):
        assert dong in th, dong
    dac = json.loads((d / "r" / "dac_ta.json").read_text(encoding="utf-8"))
    assert dac["loai_ket_cuc"] == "binary" and dac["sha256"] == sha
    assert dac["canh_bao"] == []  # «BTR» chỉ nằm ở cột nghe — không phải cột phân tích ⇒ không cảnh báo


def test_script_na_pandas_dung_danh_sach_cua_pandas(tmp_path, monkeypatch):
    pd_parsers = pytest.importorskip("pandas._libs.parsers")
    d = _de_tai(tmp_path, monkeypatch)
    assert _cu_phap() == R.MA_OK
    dong = next(
        x
        for x in _dong_thi_hanh((d / "r" / "THU_phan_tich.R").read_text(encoding="utf-8"))
        if x.startswith("NA_PANDAS <- ")
    )
    trong_script = set(json.loads("[" + dong[len("NA_PANDAS <- c(") : -1] + "]"))
    assert trong_script == set(pd_parsers.STR_NA_VALUES) and "" in trong_script


def test_script_cox_tho_tren_cung_tap_ca_voi_hieu_chinh(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch)
    assert _cu_phap() == R.MA_OK
    th = _dong_thi_hanh((d / "r" / "THU_phan_tich.R").read_text(encoding="utf-8"))
    assert "ds <- ca_du(D, c(THOI_GIAN, BIEN_CO, NHOM, hb))" in th  # dropna gồm cả hiệp biến — như Python
    assert 'KET$song_con_tho <- khoi("song_con_tho", cox(NHOM))' in th
    i = th.index("cox <- function(bien) {")
    assert "ma_tran_du_bao(ds, bien)," in " ".join(th[i : i + 3])  # mô hình thô dùng CHÍNH tập ds
    assert any('ties = "efron"' in x for x in th)


def test_script_bien_gia_bo_muc_dau_theo_ma_ky_tu(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch)
    assert _cu_phap() == R.MA_OK
    th = _dong_thi_hanh((d / "r" / "THU_phan_tich.R").read_text(encoding="utf-8"))
    assert 'for (m in sap_xep(x)[-1]) X[[paste0(b, "_", m)]] <- as.numeric(x == m)' in th
    assert 'sap_xep <- function(x) if (is.numeric(x)) sort(unique(x)) else sort(unique(x), method = "radix")' in th


def test_script_cum_cr1_va_t_g_tru_1(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch)
    assert _cu_phap() == R.MA_OK
    th = _dong_thi_hanh((d / "r" / "THU_phan_tich.R").read_text(encoding="utf-8"))
    assert 'vc_cum <- function(fit, cum) sandwich::vcovCL(fit, cluster = cum, type = "HC1", cadjust = TRUE)' in th
    assert "df_cum <- function(cum) max(length(unique(cum)) - 1, 1)" in th


def test_script_r_tu_kiem_sha_khoa_ma_3(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch)
    assert _cu_phap() == R.MA_OK
    th = _dong_thi_hanh((d / "r" / "THU_phan_tich.R").read_text(encoding="utf-8"))
    i = th.index("if (!identical(SHA_THUC, tolower(SHA256_KHOA))) {")
    assert th[i + 1].startswith('dung(3, "LOI_KHOA')


def test_cu_phap_du_lieu_doi_sau_khoa_bi_chan(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch)
    with open(d / "05_clean_locked" / "k.csv", "a", encoding="utf-8") as f:
        f.write("P5,1,40,1,khac,1,1,10,1\n")
    assert _cu_phap() == R.MA_TU_CHOI
    assert not (d / "r" / "THU_phan_tich.R").exists()


def test_cu_phap_cot_dinh_danh_bi_chan(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch, dinh_danh="y")
    assert _cu_phap() == R.MA_TU_CHOI
    assert not (d / "r" / "THU_phan_tich.R").exists()


def test_cu_phap_thieu_tu_dien_la_khong_do_duoc(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch)
    (d / "G5_REDCap_dictionary_THU.csv").unlink()
    assert _cu_phap() == R.MA_KHONG_DO


def test_cu_phap_thieu_cot_hoac_dac_ta_bi_chan(tmp_path, monkeypatch):
    _de_tai(tmp_path, monkeypatch)
    assert _cu_phap("--outcome", "khong_co") == R.MA_TU_CHOI
    _de_tai(tmp_path / "b", monkeypatch, tom={})
    assert _cu_phap() == R.MA_TU_CHOI  # không có đặc tả G6, không truyền tham số


def test_canh_bao_ma_thieu_trong_cot_phan_tich(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch)
    cb = R.canh_bao_ma_thieu("THU", d / "05_clean_locked" / "k.csv", ["nghe", "tuoi"])
    assert len(cb) == 1 and "«nghe»" in cb[0] and "«BTR»" in cb[0] and "GIÁ TRỊ THẬT" in cb[0]


def test_xac_dinh_loai_nhu_python():
    assert R.xac_dinh_loai({"outcome_type": "ordinal"}, {}) == "ordinal"
    assert R.xac_dinh_loai({"outcome_type": "auto"}, {"primary_outcome": {"outcome_type": "binary"}}) == "binary"
    assert (
        R.xac_dinh_loai({"outcome_type": "auto"}, {"primary_outcome": {"outcome_type": "categorical"}}) == "continuous"
    )
    assert R.xac_dinh_loai({"outcome_type": "auto"}, {}) == "auto"


def test_ci_welch_doi_dau_tu_chuoi_effect():
    assert R._ci_welch_tu_effect("MD=-4.508 (95%CI -6.254–-2.762)") == [2.762, 6.254]
    assert R._ci_welch_tu_effect("Median diff=1.2") is None


# ───────────── đối chiếu trên đầu ra R THẬT ─────────────


@pytest.mark.parametrize(
    "ten, so_dong",
    [("cum_logistic", 6), ("cum_tuyen_tinh", 5), ("mann_whitney", 4), ("thu_tu", 12), ("cum_thu_tu", 12), ("cox", 5)],
)
def test_doi_chieu_dau_ra_r_that_khop(ten, so_dong):
    py, r = _fx(ten)
    dong = R.doi_chieu(py, r["ket_qua"])
    assert len(dong) == so_dong
    assert all(x["trang_thai"] in ("khop", "lech_nho") for x in dong), [x for x in dong if x["trang_thai"] != "khop"]
    assert all(x["trang_thai"] == "khop" for x in dong)  # đo 14/11/2026: mọi dòng trong ngưỡng


def test_doi_chieu_lech_uoc_luong_bi_bat():
    py, r = _fx("cum_logistic")
    py["primary_outcome"]["or_crude"] = round(py["primary_outcome"]["or_crude"] * 1.05, 3)
    d = {x["muc"]: x for x in R.doi_chieu(py, r["ket_qua"])}
    assert d["Kết cục chính — OR thô (nhóm sau so nhóm trước; p χ² Yates)"]["trang_thai"] == "lech"


def test_doi_chieu_cum_khong_duoc_mien_tru_phuong_phap():
    """R tái lập ĐÚNG sandwich CR1 + t(G−1) của statsmodels ⇒ KTC cụm lệch là LỆCH, không phải «lệch nhỏ»."""
    py, r = _fx("cum_logistic")
    kq = py["multivariate"]["results"][0]
    kq["CI_95"] = [round(kq["CI_95"][0] * 0.96, 3), round(kq["CI_95"][1] * 1.04, 3)]
    nhom = next(x for x in R.doi_chieu(py, r["ket_qua"]) if x["muc"].endswith("— nhom") and "SE cụm" in x["muc"])
    assert nhom["trang_thai"] == "lech" and nhom["ghi_chu"] == ""


def test_doi_chieu_thu_tu_lech_ktc_la_lech_nho_co_ghi_chu():
    py, r = _fx("thu_tu")
    kq = py["ordinal"]["results"][0]
    kq["CI_95"] = [round(kq["CI_95"][0] * 0.97, 3), round(kq["CI_95"][1] * 1.03, 3)]
    x = R.doi_chieu(py, r["ket_qua"])[0]
    assert x["trang_thai"] == "lech_nho" and "ordinal::clm" in x["ghi_chu"]


def test_doi_chieu_so_ca_khac_la_lech_du_so_trung():
    """Bài học SPSS: HR thô trên tập ca khác vẫn có thể trùng số tình cờ — số ca khác ⇒ LỆCH."""
    py, r = _fx("cox")
    kq = copy.deepcopy(r["ket_qua"])
    kq["song_con_tho"]["n"] = 400  # R lỡ tính HR thô trên toàn bộ 400 ca, Python trên 380
    tho = next(x for x in R.doi_chieu(py, kq) if "HR thô" in x["muc"])
    assert tho["trang_thai"] == "lech" and "SỐ CA KHÁC" in tho["ghi_chu"]


def test_doi_chieu_python_khong_ra_he_so_thi_hien_dong():
    py, r = _fx("logistic_bien_chu")
    dong = R.doi_chieu(py, r["ket_qua"])
    x = next(x for x in dong if "toàn mô hình" in x["muc"])
    assert x["trang_thai"] == "khong_so_duoc" and "Python KHÔNG ra hệ số" in x["ghi_chu"]


# ───────────── lệnh chay / doi-chieu (giả lập R) — mã thoát ─────────────


def _sau_cu_phap(tmp_path, monkeypatch) -> Path:
    d = _de_tai(tmp_path, monkeypatch)
    assert _cu_phap() == R.MA_OK
    monkeypatch.setattr(R, "tim_r", lambda: Path("Rscript"))
    return d


def _gia_lap_r(monkeypatch, ma: int, tho: dict | None):
    def chay(_rs, doi_so, *, thu_muc, thoi_han=0):
        if tho is not None:
            Path(doi_so[2]).write_text(json.dumps(tho), encoding="utf-8", newline="\n")
        return ma, "XONG_R\n", "" if ma == 0 else "LOI_KHOA …"

    monkeypatch.setattr(R, "chay_r", chay)


def _tho(d: Path, **kw) -> dict:
    sha = json.loads((d / "DATA_LOCK_manifest.json").read_text(encoding="utf-8"))["sha256"]
    _py, r = _fx("cum_logistic")
    t = {
        "r_phien_ban": "R 4.6.2",
        "goi": r["goi_phien_ban"],
        "sha256_du_lieu": sha,
        "so_ca_doc": 4,
        "loai_ket_cuc": "binary",
        "ket_qua": r["ket_qua"],
        "loi": {},
        "canh_bao": [],
    }
    t.update(kw)
    return t


def _chay() -> int:
    with contextlib.redirect_stdout(io.StringIO()):
        return R.main(["chay", "--study", "THU"])


def test_lenh_chay_ma_thoat_theo_ma_cua_r(tmp_path, monkeypatch):
    d = _sau_cu_phap(tmp_path, monkeypatch)
    _gia_lap_r(monkeypatch, 0, _tho(d))
    assert _chay() == R.MA_OK
    kq = json.loads((d / "G6_r_ket_qua.json").read_text(encoding="utf-8"))
    assert kq["r_phien_ban"] == "R 4.6.2" and kq["dac_ta"]["cot_cum"] == "ban" and kq["sha256_du_lieu"]
    _gia_lap_r(monkeypatch, 3, None)
    assert _chay() == R.MA_TU_CHOI  # R từ chối vì SHA-256
    _gia_lap_r(monkeypatch, 2, None)
    assert _chay() == R.MA_KHONG_DO  # thiếu gói R
    _gia_lap_r(monkeypatch, 1, None)
    assert _chay() == R.MA_LECH
    _gia_lap_r(monkeypatch, 0, _tho(d, loi={"da_bien": "lỗi giả"}))
    assert _chay() == R.MA_LECH  # một khối R lỗi không được coi là xong


def test_lenh_chay_tu_choi_khi_khoa_doi_sau_cu_phap(tmp_path, monkeypatch):
    d = _sau_cu_phap(tmp_path, monkeypatch)
    _gia_lap_r(monkeypatch, 0, _tho(d))
    with open(d / "05_clean_locked" / "k.csv", "a", encoding="utf-8") as f:
        f.write("P9,1,40,1,khac,1,1,10,1\n")
    assert _chay() == R.MA_TU_CHOI


def _ns_doi_chieu() -> int:
    with contextlib.redirect_stdout(io.StringIO()):
        return R.main(["doi-chieu", "--study", "THU"])


def test_lenh_doi_chieu_ma_thoat(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "EXPORTS", tmp_path / "exports")
    d = tmp_path / "exports" / "THU"
    d.mkdir(parents=True)
    assert _ns_doi_chieu() == R.MA_KHONG_DO  # chưa có tệp nào
    py, r = _fx("cum_logistic")
    ket = {**r, "dac_ta": py["dac_ta_phan_tich"]}
    (d / "G6_analysis_summary.json").write_text(json.dumps(py), encoding="utf-8", newline="\n")
    (d / "G6_r_ket_qua.json").write_text(json.dumps(ket), encoding="utf-8", newline="\n")
    assert _ns_doi_chieu() == R.MA_OK
    md = (d / "G6_r_doi_chieu.md").read_text(encoding="utf-8")
    assert "6 khớp" in md and "Cần bác sĩ kiểm chứng." in md
    lech = copy.deepcopy(py)
    lech["multivariate"]["results"][0]["OR_adj"] = 2.5
    (d / "G6_analysis_summary.json").write_text(json.dumps(lech), encoding="utf-8", newline="\n")
    assert _ns_doi_chieu() == R.MA_LECH
    khac = copy.deepcopy(py)
    khac["data_lock"]["sha256"] = "0" * 64  # R và Python không cùng bộ dữ liệu khoá
    (d / "G6_analysis_summary.json").write_text(json.dumps(khac), encoding="utf-8", newline="\n")
    assert _ns_doi_chieu() == R.MA_TU_CHOI
    dt = copy.deepcopy(py)
    dt["dac_ta_phan_tich"]["covariates"] = ["tuoi"]  # đặc tả khác ⇒ không so hai phân tích khác nhau
    (d / "G6_analysis_summary.json").write_text(json.dumps(dt), encoding="utf-8", newline="\n")
    assert _ns_doi_chieu() == R.MA_TU_CHOI


# ───────────── chạy R THẬT (bỏ qua khi máy không có Rscript) ─────────────


def _co_r() -> bool:
    try:
        return bool(R.ung_vien_rscript()) and not R.kiem_moi_truong(R.tim_r())["thieu"]
    except Exception:  # noqa: BLE001
        return False


@pytest.mark.skipif(not _co_r(), reason="máy không có Rscript hoặc thiếu gói R của cầu nối")
def test_chay_that_python_den_r_khop(tmp_path, monkeypatch):
    np = pytest.importorskip("numpy")
    pd = pytest.importorskip("pandas")
    pytest.importorskip("statsmodels")
    pytest.importorskip("lifelines")
    import run_stats_analysis as RSA

    locked = {"g2_status": "LOCKED", "g4_status": "LOCKED", "g5_status": "LOCKED"}
    monkeypatch.setattr(RSA, "BASE", tmp_path)
    monkeypatch.setattr(S, "EXPORTS", tmp_path / "exports")
    monkeypatch.setattr(RSA, "_load_checkpoint", lambda study, gate: dict(locked))
    monkeypatch.setattr(RSA, "_ledger_approved", lambda *a, **k: True)
    monkeypatch.setattr(RSA.GC, "g2_quality_contract_satisfied", lambda *a, **k: True)
    monkeypatch.setattr(RSA.GC, "resolve_design_code", lambda *a, **k: ("cohort", None))
    monkeypatch.setattr(RSA.G5Q, "evaluate_study", lambda *a, **k: {"status": RSA.G5Q.STATUS_LOCKED})
    monkeypatch.setattr(
        RSA,
        "_require_locked_analysis_dataset",
        lambda study, _d: json.loads(
            (tmp_path / "exports" / study / "DATA_LOCK_manifest.json").read_text(encoding="utf-8")
        ),
    )

    rng = np.random.default_rng(20261114)
    n = 300
    ban = rng.integers(1, 13, n)
    nhom = rng.integers(0, 2, n)
    tuoi = np.round(rng.normal(55, 12, n), 1)
    gioi = rng.integers(1, 3, n)
    nghe = rng.choice(["khac", "cong_chuc", "nong_dan"], n)
    u = rng.normal(0, 0.5, 13)[ban]
    kq = (rng.random(n) < 1 / (1 + np.exp(-(-1 + 0.8 * nhom + 0.03 * (tuoi - 55) + u)))).astype(int)
    lat = 0.7 * nhom + 0.4 * (nghe == "khac") + u + rng.logistic(0, 1, n)
    t_bc = rng.exponential(1 / (0.01 * np.exp(0.6 * nhom + 0.02 * (tuoi - 55))))
    t_kd = rng.uniform(20, 200, n)
    df = pd.DataFrame(
        {
            "nhom": nhom,
            "tuoi": tuoi,
            "gioitinh": gioi,
            "nghe": nghe,
            "ban": ban,
            "kq": kq,
            "hai_long": np.digitize(lat, [-1.0, 0.0, 1.0, 2.0]) + 1,
            "thoi_gian": np.ceil(np.minimum(t_bc, t_kd) / 5) * 5,
            "bien_co": (t_bc <= t_kd).astype(int),
        }
    )
    df["tuoi"] = df["tuoi"].astype(object)
    df.loc[rng.choice(n, 15, replace=False), "tuoi"] = ""  # thiếu ⇒ Cox thô phải dùng tập ca của mô hình hiệu chỉnh

    def de_tai(study: str) -> Path:
        d = tmp_path / "exports" / study
        (d / "05_clean_locked").mkdir(parents=True)
        p = d / "05_clean_locked" / "k.csv"
        df.to_csv(p, index=False)
        (d / "DATA_LOCK_manifest.json").write_text(
            json.dumps(
                {
                    "locked_dataset_path": "05_clean_locked/k.csv",
                    "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                    "lock_date": "2026-11-14",
                }
            ),
            encoding="utf-8",
            newline="\n",
        )
        with open(d / f"G5_REDCap_dictionary_{study}.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Variable / Field Name", "Field Type", "Field Label", "Identifier?"])
            w.writerows([c, "text", c, ""] for c in df.columns)
        return p

    kich_ban = {
        # nhị phân + cụm + sống còn trong MỘT lượt Python (đủ khối: OR thô, OR/RD cụm, logistic cụm, Cox, KM)
        "THAT-NHI-COX": [
            "--outcome",
            "kq",
            "--group",
            "nhom",
            "--covariates",
            "tuoi,gioitinh",
            "--outcome-type",
            "binary",
            "--cot-cum",
            "ban",
            "--time",
            "thoi_gian",
            "--event",
            "bien_co",
        ],
        # thứ tự + biến CHỮ (biến giả bỏ mức đầu theo mã ký tự) + cụm
        "THAT-THU-TU": [
            "--outcome",
            "hai_long",
            "--group",
            "nhom",
            "--covariates",
            "tuoi,nghe",
            "--outcome-type",
            "ordinal",
            "--cot-cum",
            "ban",
        ],
    }
    for study, ts in kich_ban.items():
        p = de_tai(study)
        monkeypatch.setattr(
            sys,
            "argv",
            ["run_stats_analysis.py", "--data", str(p), "--study", study, "--gate", "G6", "--n-imputations", "2", *ts],
        )
        with contextlib.redirect_stdout(io.StringIO()):
            RSA.main()
            ma = {lenh: R.main([lenh, "--study", study]) for lenh in ("cu-phap", "chay", "doi-chieu")}
        dc = json.loads((tmp_path / "exports" / study / "G6_r_doi_chieu.json").read_text(encoding="utf-8"))
        assert ma == {"cu-phap": 0, "chay": 0, "doi-chieu": 0}, (study, ma, dc["dem"], dc.get("loi_r"))
        assert dc["dem"]["lech"] == 0 and dc["dem"]["khop"] >= 4, dc["dem"]
        muc = " | ".join(x["muc"] for x in dc["dong"])
        if study == "THAT-NHI-COX":
            assert "HR thô" in muc and "OR thô hiệu chỉnh cụm" in muc and "SE cụm" in muc
            tho = next(x for x in dc["dong"] if "HR thô" in x["muc"])
            assert tho["n"]["python"] == tho["n"]["r"] == int((df["tuoi"] != "").sum())
        else:
            assert re.search(r"— nghe_khac\b", muc) and re.search(r"— nghe_nong_dan\b", muc)
            assert "nghe_cong_chuc" not in muc  # mức đầu theo mã ký tự là tham chiếu, như pandas.get_dummies


def test_khong_doi_hanh_vi_cau_noi_spss():
    """Cầu nối R chỉ DÙNG LẠI cầu nối SPSS (không sửa): cùng ngưỡng, cùng gốc exports."""
    assert (S.TOL_UOC, S.TOL_CI, S.TOL_P) == (0.005, 0.015, 0.005)
    assert R.thu_muc_de_tai("X") == S.thu_muc_de_tai("X")
    with pytest.raises(S.TuChoi):
        R.thu_muc_de_tai("../x")
