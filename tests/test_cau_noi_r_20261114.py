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


def _de_tai(
    tmp_path: Path, monkeypatch, *, dinh_danh: str = "", tom: dict | None = None, csv_mau: str = CSV_MAU
) -> Path:
    monkeypatch.setattr(S, "EXPORTS", tmp_path / "exports")
    d = tmp_path / "exports" / "THU"
    (d / "05_clean_locked").mkdir(parents=True)
    k = d / "05_clean_locked" / "k.csv"
    k.write_text(csv_mau, encoding="utf-8", newline="")
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
        for c in csv_mau.splitlines()[0].split(","):
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


def _viet_tu_dien(d: Path, hang: list[list[str]]) -> None:
    with open(d / "G5_REDCap_dictionary_THU.csv", "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(hang)


def test_cu_phap_cot_ngoai_tu_dien_bi_chan(tmp_path, monkeypatch):
    """Lượt rà epii(a): cột CSV không có trong từ điển ⇒ trước đây coi là «không PII»."""
    d = _de_tai(tmp_path, monkeypatch)
    hang = list(csv.reader(open(d / "G5_REDCap_dictionary_THU.csv", encoding="utf-8")))
    _viet_tu_dien(d, [h for h in hang if h[0] != "record_id"])
    assert _cu_phap() == R.MA_TU_CHOI
    assert not (d / "r" / "THU_phan_tich.R").exists()
    assert R.COT_HE_THONG_REDCAP.match("phieu_a_complete") and R.COT_HE_THONG_REDCAP.match("redcap_event_name")
    assert not R.COT_HE_THONG_REDCAP.match("khao_sat_timestamp")  # mốc giờ có thể là định danh gián tiếp


def test_cu_phap_tu_dien_khong_co_cot_identifier_khong_do_duoc(tmp_path, monkeypatch):
    """Lượt rà epii(b): từ điển thiếu hẳn cột «Identifier?» ⇒ trước đây coi là «không PII»."""
    d = _de_tai(tmp_path, monkeypatch)
    _viet_tu_dien(
        d,
        [["Variable / Field Name", "Field Type", "Field Label"]]
        + [[c, "text", c] for c in CSV_MAU.splitlines()[0].split(",")],
    )
    assert _cu_phap() == R.MA_KHONG_DO
    assert not (d / "r" / "THU_phan_tich.R").exists()


def test_cu_phap_thay_placeholder_mot_luot_khong_tiem_ma(tmp_path, monkeypatch):
    """Lượt rà einj: tên cột «@@HIEP_BIEN@@» từng bị thay tiếp bằng mã R ⇒ chèn được lời gọi hàm R tuỳ ý."""
    csv_tiem = CSV_MAU.replace("kq,", "@@HIEP_BIEN@@,", 1)
    d = _de_tai(tmp_path, monkeypatch, csv_mau=csv_tiem, tom={})
    assert _cu_phap("--outcome", "@@HIEP_BIEN@@", "--group", "nhom", "--covariates", "tuoi") == R.MA_OK
    th = _dong_thi_hanh((d / "r" / "THU_phan_tich.R").read_text(encoding="utf-8"))
    assert 'KET_CUC <- "@@HIEP_BIEN@@"' in th and 'HIEP_BIEN <- c("tuoi")' in th


def test_cu_phap_hiep_bien_khong_co_trong_du_lieu_bi_tu_choi(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch)
    assert _cu_phap("--covariates", "tuoi,+file.create('x')+") == R.MA_TU_CHOI
    assert not (d / "r" / "THU_phan_tich.R").exists()


def test_script_r_chuoi_thi_hanh_chi_ascii(tmp_path, monkeypatch):
    """Ở locale C, chữ Việt viết thẳng trong chuỗi R bị đọc thành byte rời ⇒ JSON «kh<c3><b4>ng»."""
    d = _de_tai(tmp_path, monkeypatch)
    assert _cu_phap() == R.MA_OK
    th = _dong_thi_hanh((d / "r" / "THU_phan_tich.R").read_text(encoding="utf-8"))
    assert [x for x in th if not x.isascii()] == []
    assert R.ascii_hoa_chuoi_r('x <- "tuổi" # chú thích "giữ"\n') == 'x <- "tu\\u{1ed5}i" # chú thích "giữ"\n'


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
    [("cum_logistic", 7), ("cum_tuyen_tinh", 6), ("mann_whitney", 5), ("thu_tu", 13), ("cum_thu_tu", 13), ("cox", 6)],
)
def test_doi_chieu_dau_ra_r_that_khop(ten, so_dong):
    py, r = _fx(ten)
    dong = R.doi_chieu(py, r)
    assert len(dong) == so_dong
    assert [x for x in dong if x["trang_thai"] != "khop"] == []  # đo 14/11/2026: mọi dòng trong ngưỡng


def test_doi_chieu_lech_uoc_luong_bi_bat():
    py, r = _fx("cum_logistic")
    py["primary_outcome"]["or_crude"] = round(py["primary_outcome"]["or_crude"] * 1.05, 3)
    d = {x["muc"]: x for x in R.doi_chieu(py, r)}
    assert d["Kết cục chính — OR thô (nhóm sau so nhóm trước; p χ² Yates)"]["trang_thai"] == "lech"


def test_doi_chieu_cum_lech_ktc_la_lech():
    """R tái lập ĐÚNG sandwich CR1 + t(G−1) của statsmodels ⇒ KTC cụm lệch là LỆCH."""
    py, r = _fx("cum_logistic")
    kq = py["multivariate"]["results"][0]
    kq["CI_95"] = [round(kq["CI_95"][0] * 0.96, 3), round(kq["CI_95"][1] * 1.04, 3)]
    nhom = next(x for x in R.doi_chieu(py, r) if x["muc"].endswith("— nhom") and "SE cụm" in x["muc"])
    assert nhom["trang_thai"] == "lech" and nhom["ghi_chu"] == ""


def test_doi_chieu_thu_tu_khong_con_mien_tru_phuong_phap():
    """Đo thật: KTC thứ tự R ↔ statsmodels lệch ≤ 0,5 % ⇒ không cần miễn trừ; KTC cụm lệch 3 % là LỆCH."""
    py, r = _fx("cum_thu_tu")
    kq = py["ordinal"]["results"][0]
    kq["CI_95"] = [round(kq["CI_95"][0] * 0.97, 3), round(kq["CI_95"][1] * 1.03, 3)]
    dong = R.doi_chieu(py, r)
    x = next(x for x in dong if "SE cụm" in x["muc"])
    assert x["trang_thai"] == "lech" and x["ghi_chu"] == ""
    assert all(x["trang_thai"] in ("khop", "lech", "khong_so_duoc") for x in dong)  # không còn «lệch nhỏ»


def test_so_p_r_them_dieu_kien_tuong_doi_cho_p_nho():
    assert S._so_p(0.0002, 0.0018) is True  # luật SPSS (giữ nguyên) coi là khớp …
    assert R._so_p_r(0.0002, 0.0018) is False  # … luật R thì không
    assert R._so_p_r(0.0004, 0.0) is False  # Python 0,0 nghĩa là < 0,00005
    assert R._so_p_r(1.5e-7, 0.0) and R._so_p_r(5.231e-05, 0.0001) and R._so_p_r(0.01269, 0.0127)
    assert R._so_p_r(0.30, 0.296) and not R._so_p_r(0.30, 0.31)


def test_doi_chieu_so_ca_khac_la_lech_du_so_trung():
    """Bài học SPSS: HR thô trên tập ca khác vẫn có thể trùng số tình cờ — số ca khác ⇒ LỆCH."""
    py, r = _fx("cox")
    r["ket_qua"]["song_con_tho"]["n"] = 400  # R lỡ tính HR thô trên toàn bộ 400 ca, Python trên 380
    tho = next(x for x in R.doi_chieu(py, r) if "HR thô" in x["muc"])
    assert tho["trang_thai"] == "lech" and "SỐ CA KHÁC" in tho["ghi_chu"]


def test_doi_chieu_so_ca_doc_khac_la_lech():
    py, r = _fx("cox")
    r["so_ca_doc"] = py["n_total"] - 1  # R đọc thiếu một dòng (vd hiểu khác chuỗi thiếu của pandas)
    assert R.doi_chieu(py, r)[0]["trang_thai"] == "lech"


# ───────────── ĐỎ 1: mục chỉ MỘT phía ra số không được im lặng ─────────────


def _mot(dong: list[dict], *chuoi: str) -> dict:
    return next(x for x in dong if all(c in x["muc"] for c in chuoi))


def test_doi_chieu_python_khong_ra_he_so_thi_hien_dong():
    py, r = _fx("logistic_bien_chu")
    x = _mot(R.doi_chieu(py, r), "toàn mô hình")
    assert x["trang_thai"] == "khong_so_duoc" and "Python KHÔNG ra hệ số" in x["ghi_chu"]


def test_doi_chieu_python_sap_hoi_quy_thu_tu_hien_dong():
    """Lượt rà e12: OrderedModel lỗi (hiệp biến hằng) ⇒ trước đây mã 0 «2 khớp»."""
    py, r = _fx("thu_tu")
    py["ordinal"] = {"error": "Hồi quy thứ tự không chạy được: There should not be a constant in the model"}
    x = _mot(R.doi_chieu(py, r), "ordinal_logit_po", "toàn mô hình")
    assert x["trang_thai"] == "khong_so_duoc" and "Python KHÔNG ra hệ số" in x["ghi_chu"]


def test_doi_chieu_python_sap_cox_nhom_chu_hien_dong_va_tim_bien_gia():
    """Lượt rà e2: nhóm A/B ⇒ lifelines lỗi, R ghi hệ số «nhom_B» ⇒ trước đây bỏ im lặng."""
    py, r = _fx("cox")
    py["survival"] = {
        "n": 380,
        "group_col": "nhom",
        "crude_error": "could not convert string to float: 'B'",
        "adjusted_error": "could not convert string to float: 'B'",
    }
    for k in ("song_con_tho", "song_con_hieu_chinh"):
        r["ket_qua"][k]["he_so"] = {"nhom_B": r["ket_qua"][k]["he_so"]["nhom"]}
    cox = [x for x in R.doi_chieu(py, r) if x["muc"].startswith("Cox")]
    assert len(cox) == 2
    for x in cox:
        assert x["trang_thai"] == "khong_so_duoc" and "Python KHÔNG ra HR" in x["ghi_chu"]
        assert "nhom_B" in x["ghi_chu"] and x["r"]["uoc_luong"] is not None


def test_doi_chieu_bien_gia_nhom_chu_khi_hai_phia_cung_ra_so():
    py, r = _fx("cox")
    for k in ("song_con_tho", "song_con_hieu_chinh"):
        r["ket_qua"][k]["he_so"] = {"nhom_B": r["ket_qua"][k]["he_so"]["nhom"]}
    x = _mot(R.doi_chieu(py, r), "HR thô")
    assert x["trang_thai"] == "khop" and "(R: nhom_B)" in x["muc"]


def test_doi_chieu_ket_cuc_chinh_mot_phia():
    py, r = _fx("cum_logistic")
    p1 = copy.deepcopy(py)
    p1["primary_outcome"] = {"error": "Nhóm '1' không còn quan sát nào"}
    d1 = R.doi_chieu(p1, r)
    assert "Python KHÔNG ra kết cục chính" in _mot(d1, "Kết cục chính")["ghi_chu"]
    assert _mot(d1, "hiệu chỉnh cụm")["trang_thai"] == "khong_so_duoc"
    p2 = copy.deepcopy(py)
    del p2["primary_outcome"]["or_crude"]  # một nhóm 0 % biến cố ⇒ Python không tính OR
    x = _mot(R.doi_chieu(p2, r), "OR thô (nhóm sau")
    assert x["trang_thai"] == "khong_so_duoc" and "Python không tính OR thô" in x["ghi_chu"]
    r3 = copy.deepcopy(r)
    del r3["ket_qua"]["ket_cuc_chinh"]
    r3["loi"] = {"ket_cuc_chinh": "lỗi giả"}
    assert "R KHÔNG ra kết cục chính: lỗi giả" in _mot(R.doi_chieu(py, r3), "Kết cục chính")["ghi_chu"]


def test_doi_chieu_he_so_hai_chieu():
    py, r = _fx("cum_logistic")
    p1 = copy.deepcopy(py)
    p1["multivariate"]["results"] = [x for x in p1["multivariate"]["results"] if x["variable"] != "gioitinh"]
    x = _mot(R.doi_chieu(p1, r), "SE cụm", "gioitinh")
    assert x["trang_thai"] == "khong_so_duoc" and "Python không có hệ số này" in x["ghi_chu"]
    r2 = copy.deepcopy(r)
    del r2["ket_qua"]["da_bien_cum"]
    r2["loi"] = {"da_bien": "lỗi giả"}
    x = _mot(R.doi_chieu(py, r2), "toàn mô hình")
    assert x["trang_thai"] == "khong_so_duoc" and "R KHÔNG ra hệ số: lỗi giả" in x["ghi_chu"]


def test_dong_ktc_hoac_p_mot_phia_khong_cham_khop():
    x = R._dong("t", {"uoc_luong": 1.0, "ci": [0.5, 2.0], "p": 0.2}, {"uoc_luong": 1.0, "ci": None, "p": 0.2})
    assert x["trang_thai"] == "khong_so_duoc" and "KTC chỉ có ở phía Python" in x["ghi_chu"]
    x = R._dong("t", {"uoc_luong": 1.0, "ci": None, "p": None}, {"uoc_luong": 1.0, "ci": None, "p": 0.2})
    assert x["trang_thai"] == "khong_so_duoc" and "p chỉ có ở phía R" in x["ghi_chu"]
    x = R._dong("t", {"uoc_luong": 1.0, "ci": [0.5, 2.0]}, {"uoc_luong": 1.0, "ci": [0.5, None]})
    assert x["trang_thai"] == "khong_so_duoc"  # cận vô hạn (null) ở R


def test_km_trung_vi_so_ca_log_rank_va_diem_bien():
    py, r = _fx("cox")
    km, rk = py["kaplan_meier"], r["ket_qua"]["kaplan_meier"]
    g0 = next(y for y in rk["nhom"] if float(y["gia_tri"]) == 0)
    tv = g0["trung_vi"]
    # chưa đạt trung vị ở cả hai phía vẫn phải so SỐ CA
    p1, r1 = copy.deepcopy(py), copy.deepcopy(r)
    p1["kaplan_meier"]["groups"]["0"]["median_survival"] = None
    y = next(y for y in r1["ket_qua"]["kaplan_meier"]["nhom"] if float(y["gia_tri"]) == 0)
    y.update(trung_vi=None, n=y["n"] + 1)
    assert _mot(R.doi_chieu(p1, r1), "nhóm 0")["trang_thai"] == "lech"
    # log-rank có so số ca
    r2 = copy.deepcopy(r)
    r2["ket_qua"]["kaplan_meier"]["logrank_n"] = rk["logrank_n"] - 1
    assert _mot(R.doi_chieu(py, r2), "log-rank")["trang_thai"] == "lech"
    # điểm biên S(t) = 0,5: chấp nhận thời điểm kề R đã ghi, kèm ghi chú
    p3, r3 = copy.deepcopy(py), copy.deepcopy(r)
    p3["kaplan_meier"]["groups"]["0"]["median_survival"] = tv + 5
    y = next(y for y in r3["ket_qua"]["kaplan_meier"]["nhom"] if float(y["gia_tri"]) == 0)
    y["trung_vi_thay_the"] = tv + 5
    x = _mot(R.doi_chieu(p3, r3), "nhóm 0")
    assert x["trang_thai"] == "khop" and "điểm biên" in x["ghi_chu"]
    y["trung_vi_thay_the"] = None
    assert _mot(R.doi_chieu(p3, r3), "nhóm 0")["trang_thai"] == "lech"
    assert km["logrank_p"] is not None


# ───────────── hàm R dùng chung: so với lifelines / scipy (cần R) ─────────────


def _co_r() -> bool:
    try:
        return bool(R.ung_vien_rscript()) and not R.kiem_moi_truong(R.tim_r())["thieu"]
    except Exception:  # noqa: BLE001
        return False


CO_R = _co_r()


def _chay_ham_r(tmp_path: Path, vao: dict, than: str) -> dict:
    """Trích khối «ham-kiem-thu» từ MAU_R (đúng mã script sinh ra dùng) rồi chạy với dữ liệu `vao`."""
    a, b = R.MAU_R.index("# >>> ham-kiem-thu"), R.MAU_R.index("# <<< ham-kiem-thu")
    (tmp_path / "vao.json").write_text(json.dumps(vao), encoding="utf-8", newline="\n")
    ma = (
        "suppressPackageStartupMessages(library(survival))\n"
        + R.ascii_hoa_chuoi_r(R.MAU_R[a:b])
        + 'V <- jsonlite::read_json("vao.json", simplifyVector = TRUE)\n'
        + than
        + '\njsonlite::write_json(RA, "ra.json", auto_unbox = TRUE, digits = NA, na = "null")\n'
    )
    (tmp_path / "t.R").write_text(ma, encoding="utf-8", newline="\n")
    kq = R.chay_r(R.tim_r(), [str(tmp_path / "t.R")], thu_muc=tmp_path, thoi_han=120)
    assert kq[0] == 0, kq[2]
    return json.loads((tmp_path / "ra.json").read_text(encoding="utf-8"))


@pytest.mark.skipif(not CO_R, reason="máy không có Rscript hoặc thiếu gói R của cầu nối")
def test_trung_vi_km_nhu_lifelines_ke_ca_diem_bien(tmp_path):
    lifelines = pytest.importorskip("lifelines")
    ca = {
        "bien_6": [[1, 2, 3, 4, 5, 6], [1, 1, 1, 1, 1, 1]],  # S(3) = 0,5 đúng: lifelines ra 0,5000000000000001 ⇒ 4
        "kiem_duyet": [[1, 2, 3, 4, 5, 6, 7, 8], [1, 1, 0, 1, 1, 1, 1, 1]],
        "chua_dat": [[5, 10, 15, 20], [1, 0, 0, 0]],
        "trung": [[5, 5, 10, 10, 10, 15, 20, 20, 25, 30], [1, 1, 1, 0, 1, 1, 0, 1, 1, 0]],
    }
    ra = _chay_ham_r(
        tmp_path,
        ca,
        (
            "RA <- lapply(V, function(x) {\n"
            "  sf <- survival::survfit(Surv(x[1, ], x[2, ]) ~ 1)\n"
            "  trung_vi_lifelines(sf$time, sf$n.risk, sf$n.event)\n"
            "})"
        ),
    )
    for ten, (t, e) in ca.items():
        tv_ll = lifelines.KaplanMeierFitter().fit(t, e).median_survival_time_
        tv_r = ra[ten]["tv"]
        assert (tv_r is None and tv_ll == float("inf")) or tv_r == tv_ll, (ten, tv_r, tv_ll)
    assert ra["bien_6"]["thay"] == 3  # thời điểm kề ở điểm biên được ghi kèm


@pytest.mark.skipif(not CO_R, reason="máy không có Rscript hoặc thiếu gói R của cầu nối")
def test_mann_whitney_nhu_scipy_chon_dung_phuong_phap(tmp_path):
    st = pytest.importorskip("scipy.stats")
    np = pytest.importorskip("numpy")
    rng = np.random.default_rng(3)
    ca = {
        "nho_khong_trung": [[1.2, 3.4, 2.2, 5.1, 0.7, 4.4], [2.9, 6.1, 7.3, 5.5, 8.8, 3.3, 9.1]],
        "nho_co_trung": [[1, 2, 2, 3, 4, 5], [3, 4, 4, 6, 7, 8, 9]],
        "lon": [rng.lognormal(0, 1, 40).round(3).tolist(), rng.lognormal(0.4, 1, 45).round(3).tolist()],
    }
    ra = _chay_ham_r(
        tmp_path,
        {k: {"a": a, "b": b} for k, (a, b) in ca.items()},
        "RA <- lapply(V, function(x) p_mann_whitney(x$a, x$b))",
    )
    for ten, (a, b) in ca.items():
        kq = st.mannwhitneyu(a, b, alternative="two-sided")
        assert ra[ten]["p"] == pytest.approx(float(kq.pvalue), rel=1e-9), ten
    assert ra["nho_khong_trung"]["phuong_phap"] == "exact" and ra["nho_co_trung"]["phuong_phap"] == "asymptotic"
    assert ra["lon"]["phuong_phap"] == "asymptotic"


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


def test_lenh_chay_mot_canh_bao_khong_bi_tach_ky_tu(tmp_path, monkeypatch):
    """jsonlite auto_unbox biến mảng MỘT phần tử thành chuỗi — không được `list()` thành từng ký tự."""
    d = _sau_cu_phap(tmp_path, monkeypatch)
    _gia_lap_r(monkeypatch, 0, _tho(d, canh_bao="da_bien: glm.fit: fitted probabilities numerically 0 or 1"))
    assert _chay() == R.MA_OK
    cb = json.loads((d / "G6_r_ket_qua.json").read_text(encoding="utf-8"))["canh_bao"]
    assert "da_bien: glm.fit: fitted probabilities numerically 0 or 1" in cb and "d" not in cb


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

    def ghi(tom: dict) -> int:
        (d / "G6_analysis_summary.json").write_text(json.dumps(tom), encoding="utf-8", newline="\n")
        (d / "G6_r_ket_qua.json").write_text(json.dumps(ket), encoding="utf-8", newline="\n")
        return _ns_doi_chieu()

    assert ghi(py) == R.MA_OK
    md = (d / "G6_r_doi_chieu.md").read_text(encoding="utf-8")
    assert "7 khớp" in md and "Cần bác sĩ kiểm chứng." in md
    lech = copy.deepcopy(py)
    lech["multivariate"]["results"][0]["OR_adj"] = 2.5
    assert ghi(lech) == R.MA_LECH
    sap = copy.deepcopy(py)
    sap["multivariate"] = {"error": "Pandas data cast to numpy dtype of object"}  # Python sập mô hình chính
    assert ghi(sap) == R.MA_KHONG_DO  # KHÔNG được báo 0 «khớp»
    assert "CHƯA đối chiếu trọn" in (d / "G6_r_doi_chieu.md").read_text(encoding="utf-8")
    khac = copy.deepcopy(py)
    khac["data_lock"]["sha256"] = "0" * 64  # R và Python không cùng bộ dữ liệu khoá
    assert ghi(khac) == R.MA_TU_CHOI
    dt = copy.deepcopy(py)
    dt["dac_ta_phan_tich"]["covariates"] = ["tuoi"]  # đặc tả khác ⇒ không so hai phân tích khác nhau
    assert ghi(dt) == R.MA_TU_CHOI


# ───────────── chạy R THẬT: run_stats_analysis.py → cu-phap → chay → doi-chieu ─────────────


def _du_lieu_that():
    np = pytest.importorskip("numpy")
    pd = pytest.importorskip("pandas")
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
            "nhom_chu": np.where(nhom == 1, "B", "A"),
            "tuoi": tuoi,
            "gioitinh": gioi,
            "gioi_hang": 2,
            "nghe": nghe,
            "ban": ban,
            "kq": kq,
            "diem": np.round(50 + 4 * nhom + 0.2 * (tuoi - 55) + rng.normal(0, 8, n), 2),
            "diem_lech": np.round(np.exp(1 + 0.3 * nhom + rng.normal(0, 0.9, n)), 2),
            "hai_long": np.digitize(lat, [-1.0, 0.0, 1.0, 2.0]) + 1,
            "thoi_gian": np.ceil(np.minimum(t_bc, t_kd) / 5) * 5,
            "bien_co": (t_bc <= t_kd).astype(int),
        }
    )
    df["tuoi"] = df["tuoi"].astype(object)
    df.loc[rng.choice(n, 15, replace=False), "tuoi"] = ""  # thiếu ⇒ Cox thô phải dùng tập ca của mô hình hiệu chỉnh
    return df


KICH_BAN_THAT = {
    # nhị phân + cụm + sống còn trong MỘT lượt Python (OR thô, OR/RD cụm, logistic cụm, Cox, KM)
    "NHI-CUM-COX": (
        [
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
        0,
        ("HR thô", "SE cụm"),
    ),
    "LOGISTIC": (
        ["--outcome", "kq", "--group", "nhom", "--covariates", "tuoi,gioitinh", "--outcome-type", "binary"],
        0,
        ("Đa biến (logistic) — nhom",),
    ),
    "WELCH": (
        ["--outcome", "diem", "--group", "nhom", "--covariates", "tuoi,gioitinh", "--outcome-type", "continuous"],
        0,
        ("Welch", "Đa biến (linear) — nhom"),
    ),
    "MANN-WHITNEY": (
        ["--outcome", "diem_lech", "--group", "nhom", "--covariates", "tuoi,gioitinh", "--outcome-type", "continuous"],
        0,
        ("Mann–Whitney",),
    ),
    # thứ tự + biến CHỮ (biến giả bỏ mức đầu theo mã ký tự): có cụm và không cụm (HC3)
    "THU-TU-CUM": (
        [
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
        0,
        ("SE cụm", "— nghe_khac", "Nhạy cảm OLS (cluster)"),
    ),
    "THU-TU-HC3": (
        ["--outcome", "hai_long", "--group", "nhom", "--covariates", "tuoi,nghe", "--outcome-type", "ordinal"],
        0,
        ("— nghe_nong_dan", "Nhạy cảm OLS (HC3)"),
    ),
    # Python sập mô hình chính mà R chạy được ⇒ doi-chieu mã 2, có dòng «Python KHÔNG ra …» (lượt rà e12, e2)
    "PY-SAP-THU-TU": (
        ["--outcome", "hai_long", "--group", "nhom", "--covariates", "tuoi,gioi_hang", "--outcome-type", "ordinal"],
        2,
        ("toàn mô hình",),
    ),
    "PY-SAP-COX": (
        ["--group", "nhom_chu", "--covariates", "tuoi", "--time", "thoi_gian", "--event", "bien_co"],
        2,
        ("HR thô",),
    ),
}


@pytest.mark.skipif(not CO_R, reason="máy không có Rscript hoặc thiếu gói R của cầu nối")
@pytest.mark.parametrize("ten", list(KICH_BAN_THAT))
def test_chay_that_python_den_r(ten, tmp_path, monkeypatch):
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
    df = _du_lieu_that()
    study = "THAT-" + ten
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
    tham_so, ma_ky_vong, phai_co = KICH_BAN_THAT[ten]
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_stats_analysis.py", "--data", str(p), "--study", study, "--gate", "G6", "--n-imputations", "2", *tham_so],
    )
    with contextlib.redirect_stdout(io.StringIO()):
        RSA.main()
        ma = {lenh: R.main([lenh, "--study", study]) for lenh in ("cu-phap", "chay", "doi-chieu")}
    dc = json.loads((d / "G6_r_doi_chieu.json").read_text(encoding="utf-8"))
    assert ma == {"cu-phap": 0, "chay": 0, "doi-chieu": ma_ky_vong}, (ma, dc["dem"], dc.get("loi_r"))
    muc = " | ".join(x["muc"] for x in dc["dong"])
    assert all(c in muc for c in phai_co), muc
    assert dc["dem"]["lech"] == 0, [x for x in dc["dong"] if x["trang_thai"] == "lech"]
    if ma_ky_vong == 0:
        assert dc["dem"]["khop"] == len(dc["dong"]) >= 4  # MỌI dòng khớp — không «lệch nhỏ», không bỏ sót
    else:
        sap = [x for x in dc["dong"] if x["trang_thai"] == "khong_so_duoc"]
        assert sap and all("Python KHÔNG ra" in x["ghi_chu"] for x in sap if "HR" in x["muc"] or "toàn" in x["muc"])
    if ten == "NHI-CUM-COX":
        tho = next(x for x in dc["dong"] if "HR thô" in x["muc"])
        assert tho["n"]["python"] == tho["n"]["r"] == int((df["tuoi"] != "").sum())
    if ten.startswith("THU-TU"):
        assert "nghe_cong_chuc" not in muc  # mức đầu theo mã ký tự là tham chiếu, như pandas.get_dummies
    if ten == "PY-SAP-COX":
        assert "nhom_chu_B" in " ".join(x["ghi_chu"] for x in dc["dong"])


def test_khong_doi_hanh_vi_cau_noi_spss():
    """Cầu nối R chỉ DÙNG LẠI cầu nối SPSS (không sửa): cùng ngưỡng, cùng gốc exports."""
    assert (S.TOL_UOC, S.TOL_CI, S.TOL_P) == (0.005, 0.015, 0.005)
    assert R.thu_muc_de_tai("X") == S.thu_muc_de_tai("X")
    with pytest.raises(S.TuChoi):
        R.thu_muc_de_tai("../x")
