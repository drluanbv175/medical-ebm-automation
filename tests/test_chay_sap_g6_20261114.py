"""F3 (14/11/2026) — chạy trọn SAP G6 bằng một lệnh: tools/chay_sap_g6.py + lọc quần thể --loc + kiểm chéo theo gate.

Soát chuỗi SPSS/R theo yêu cầu bác sĩ: SAP thật cam kết nhiều phân tích (chính · phụ · nhóm con · độ nhạy, nhiều mục
trên quần thể con «PhieuHopLe == 1», «vao_truoc_0107 == 1»…) nhưng run_stats_analysis chạy một đặc tả mỗi lần, không lọc
được quần thể, kiểm chéo ghi đè nhau (G6_kiem_cheo.json cố định) và cầu nối từ chối khi phơi nhiễm liên tục. Dữ liệu
giả, không PII; cổng G2/G4/G5 giả lập như các test run_stats sẵn có.
"""

from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
np = pytest.importorskip("numpy")
pd = pytest.importorskip("pandas")
pytest.importorskip("statsmodels")
import bien_phai_sinh as B  # noqa: E402
import cau_noi_r as R  # noqa: E402
import cau_noi_spss as S  # noqa: E402
import chay_sap_g6 as CS  # noqa: E402
import kiem_cheo_g6 as KC  # noqa: E402
import run_stats_analysis as RSA  # noqa: E402

COT_TD = ["Variable / Field Name", "Form Name", "Field Type", "Field Label", "Choices, Calculations, OR Slider Labels",
          "Text Validation Type OR Show Slider Number", "Identifier?", "Field Annotation"]  # fmt: skip


def _de_tai(goc: Path, duyet_ps: bool = True) -> Path:
    d = goc / "exports" / "SAP"
    (d / "05_clean_locked").mkdir(parents=True)
    rng = np.random.default_rng(14)
    n = 300
    g1 = rng.choice([1, 2, 3, 4, 5], n).astype(object)
    g1[:8] = None
    df = pd.DataFrame({"cho": rng.uniform(5, 150, n).round(1), "kg": rng.choice([1, 2, 3], n),
                       "mode": rng.choice([1, 1, 2], n), "g1": g1, "nhom": rng.integers(0, 2, n)})  # fmt: skip
    k = d / "05_clean_locked" / "k.csv"
    df.to_csv(k, index=False)
    (d / "DATA_LOCK_manifest.json").write_text(json.dumps({
        "locked_dataset_path": "05_clean_locked/k.csv", "sha256": hashlib.sha256(k.read_bytes()).hexdigest(),
        "lock_date": "2026-11-14", "status": "LOCKED_FOR_ANALYSIS", "analysis_allowed": True}), encoding="utf-8",
        newline="\n")  # fmt: skip
    with open(d / "G5_REDCap_dictionary_SAP.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(COT_TD)
        for t, loai, lc in [("cho", "text", ""), ("kg", "radio", "1, a | 2, b | 3, c"),
                            ("mode", "radio", "1, a | 2, b"), ("g1", "radio", "1, a | 2, b | 3, c | 4, d | 5, e"),
                            ("nhom", "radio", "0, A | 1, B")]:
            w.writerow([t, "f", loai, t, lc, "", "", ""])
    ct = "neu(la_thieu(g1), 0, 1)"
    with open(d / "_bien-phai-sinh.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ten_bien", "nhan", "kieu", "dinh_nghia", "bien_nguon", "quy_tac_ma_thieu", "dung_o", "nguon",
                    "cong_thuc", "lap_k", "nhan_gia_tri", "nguoi_duyet"])  # fmt: skip
        w.writerow(["hop_le", "hl", "", "", "", "", "", "", ct, "", "",
                    f"TKV:T:2026-11-14:{B.dau_cong_thuc('hop_le', ct, '')}" if duyet_ps else ""])  # fmt: skip
    sap = d / "G4_A5_SAP_FINAL_SAP.md"
    sap.write_text("# SAP\n§4\n", encoding="utf-8", newline="\n")
    return d


def _dac_ta(d: Path, duyet: bool = True, **sua) -> dict:
    sap = d / "G4_A5_SAP_FINAL_SAP.md"
    dt = {"nguon_sap": sap.name, "sha256_sap": hashlib.sha256(sap.read_bytes()).hexdigest(), "phan_tich": [
        {"id": "chinh", "vai": "chinh", "sap_muc": "§4", "mo_ta": "thứ tự",
         "tham_so": {"outcome": "g1", "group": "cho", "covariates": ["kg"], "hiep_bien_phan_loai": ["kg"],
                     "outcome_type": "ordinal", "loc": "hop_le == 1", "n_imputations": 2}},
        {"id": "dn_tu", "vai": "do_nhay", "sap_muc": "§9", "mo_ta": "tự điền",
         "tham_so": {"outcome": "g1", "group": "cho", "covariates": ["kg"], "hiep_bien_phan_loai": ["kg"],
                     "outcome_type": "ordinal", "loc": "hop_le == 1 and mode == 1", "n_imputations": 2}},
        {"id": "ty_le", "vai": "mo_ta", "sap_muc": "§3", "mo_ta": "tỷ lệ",
         "tham_so": {"ty_le": ["g1"], "nguong_ty_le": 4, "loc": "hop_le == 1"}},
        {"id": "spline", "vai": "do_nhay", "sap_muc": "§9", "mo_ta": "phi tuyến", "chua_tu_dong": "chưa có RCS"}]}
    dt.update(sua)
    if duyet:
        dt["nguoi_duyet"] = f"THONG_KE_VIEN:T:2026-11-14:{CS.dau_dac_ta(dt)}"
    (d / CS.TEP_DAC_TA).write_text(json.dumps(dt, ensure_ascii=False), encoding="utf-8", newline="\n")
    return dt


# ───────────────────────── kiểm đặc tả ─────────────────────────


def test_dac_ta_hop_le_dau_va_sap_doi(tmp_path):
    d = _de_tai(tmp_path)
    dt = _dac_ta(d)
    k = CS.kiem_dac_ta(d, dt)
    assert k["loi"] == [] and k["duyet"] == "DA_DUYET" and k["sap_khop"] is True
    (d / "G4_A5_SAP_FINAL_SAP.md").write_text("# SAP sửa đổi\n", encoding="utf-8", newline="\n")
    assert any("SAP đã ĐỔI" in x for x in CS.kiem_dac_ta(d, dt)["loi"])
    dt2 = dict(dt, phan_tich=dt["phan_tich"][:1])  # sửa đặc tả sau khi duyệt ⇒ dấu đổi
    assert CS.kiem_dac_ta(d, dt2)["duyet"] == "HET_HIEU_LUC"


@pytest.mark.parametrize(
    "sua, mau",
    [
        ({"tham_so": {"outcome": "g1", "la": 1}}, "không hỗ trợ: la"),
        ({"tham_so": {"outcome": "--i-confirm-sap-locked"}}, "tên cột hợp lệ"),
        ({"tham_so": {"outcome": "g1", "covariates": ["a", "-x"]}}, "danh sách tên"),
        ({"tham_so": {"outcome": "g1", "loc": "1 < g1 < 3"}}, "loc:"),
        ({"tham_so": {"outcome": "g1", "outcome_type": "logit"}}, "outcome_type phải"),
        ({"tham_so": {"time": "t"}}, "time và event"),
        ({"tham_so": {"group": "cho"}}, "cần outcome"),
        ({"tham_so": {"outcome": "g1", "n_imputations": 999}}, "0–200"),
        # «--i-confirm-sap-locked» là biểu thức số học HỢP LỆ (−(−i) − confirm …) ⇒ chỉ rào «-» chặn được
        ({"tham_so": {"outcome": "g1", "loc": "--i-confirm-sap-locked"}}, "không bắt đầu bằng"),
    ],
)
def test_dac_ta_sai_bi_bat(tmp_path, sua, mau):
    d = _de_tai(tmp_path)
    dt = _dac_ta(d)
    dt["phan_tich"][1] = {"id": "x", "vai": "phu", "sap_muc": "§5", "mo_ta": "m", **sua}
    assert any(mau in x for x in CS.kiem_dac_ta(d, dt)["loi"]), CS.kiem_dac_ta(d, dt)["loi"]


def test_dac_ta_dung_mot_chinh_va_chua_tu_dong(tmp_path):
    d = _de_tai(tmp_path)
    dt = _dac_ta(d)
    dt["phan_tich"][1]["vai"] = "chinh"
    assert any("ĐÚNG một" in x for x in CS.kiem_dac_ta(d, dt)["loi"])
    dt = _dac_ta(d)
    dt["phan_tich"][3]["tham_so"] = {"outcome": "g1"}
    assert any("không khai tham_so" in x for x in CS.kiem_dac_ta(d, dt)["loi"])
    dt = _dac_ta(d)
    dt["phan_tich"].append(dict(dt["phan_tich"][2]))
    assert any("id trùng" in x for x in CS.kiem_dac_ta(d, dt)["loi"])


def test_doi_so_run_stats_va_gate():
    pt = {"id": "a", "vai": "phu", "tham_so": {"outcome": "y", "covariates": ["a", "b"], "ty_le": ["y", "z"],
                                               "don_vi_phoi_nhiem": 15, "nguong_ty_le": 4.5, "loc": "h == 1"}}
    ds = CS.doi_so_run_stats(pt)
    assert ds == ["--outcome", "y", "--covariates", "a,b", "--ty-le", "y", "z", "--don-vi-phoi-nhiem", "15",
                  "--nguong-ty-le", "4.5", "--loc", "h == 1"]  # fmt: skip
    assert CS.gate_cua(pt) == "G6_a" and CS.gate_cua({"id": "x", "vai": "chinh"}) == "G6"


# ───────────────────────── chạy (run_stats trong tiến trình, cổng giả lập) ─────────────────────────


def _vao_tien_trinh(monkeypatch, goc: Path, d: Path):
    locked = {"g2_status": "LOCKED", "g4_status": "LOCKED", "g5_status": "LOCKED"}
    man = json.loads((d / "DATA_LOCK_manifest.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(RSA, "BASE", goc)
    monkeypatch.setattr(RSA, "_load_checkpoint", lambda s, g: dict(locked))
    monkeypatch.setattr(RSA, "_ledger_approved", lambda *a, **k: True)
    monkeypatch.setattr(RSA.GC, "g2_quality_contract_satisfied", lambda *a, **k: True)
    monkeypatch.setattr(RSA.GC, "resolve_design_code", lambda *a, **k: ("cross_sectional", None))
    monkeypatch.setattr(RSA.G5Q, "evaluate_study", lambda *a, **k: {"status": RSA.G5Q.STATUS_LOCKED})
    monkeypatch.setattr(RSA, "_require_locked_analysis_dataset", lambda s, _d: man)
    monkeypatch.setattr(S, "EXPORTS", goc / "exports")
    monkeypatch.setattr(CS, "BASE", goc)
    goi: list[list[str]] = []

    def chay_trong(lenh, **kw):
        goi.append(lenh)
        out, err, ma = io.StringIO(), io.StringIO(), 0
        cu = sys.argv
        sys.argv = ["run_stats_analysis.py", *lenh[2:]]
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                RSA.main()
        except SystemExit as e:
            ma = e.code or 0
        finally:
            sys.argv = cu
        return subprocess.CompletedProcess(lenh, ma, out.getvalue(), err.getvalue())

    monkeypatch.setattr(CS.subprocess, "run", chay_trong)
    return goi


def test_chay_tron_sap_ghi_chi_muc(tmp_path, monkeypatch):
    d = _de_tai(tmp_path)
    _dac_ta(d)
    goi = _vao_tien_trinh(monkeypatch, tmp_path, d)
    with contextlib.redirect_stdout(io.StringIO()):
        assert CS.main(["chay", "--study", "SAP"]) == 0
    cm = json.loads((d / CS.TEP_KQ_JSON).read_text(encoding="utf-8"))
    tt = {x["id"]: (x["trang_thai"], x.get("gate")) for x in cm["phan_tich"]}
    assert tt == {"chinh": ("DA_CHAY", "G6"), "dn_tu": ("DA_CHAY", "G6_dn_tu"), "ty_le": ("DA_CHAY", "G6_ty_le"),
                  "spline": ("CHUA_TU_DONG", None)}  # fmt: skip
    assert cm["dem"] == {"DA_CHAY": 3, "LOI": 0, "CHUA_TU_DONG": 1}
    assert (d / "G6_analysis_summary.json").is_file() and (d / "G6_dn_tu_analysis_summary.json").is_file()
    n = {x["id"]: x["uoc_luong"]["n_total"] for x in cm["phan_tich"] if x["trang_thai"] == "DA_CHAY"}
    assert n["chinh"] == 292 and n["dn_tu"] < n["chinh"]  # lọc quần thể có hiệu lực
    assert not [x for lenh in goi for x in lenh if x.startswith("--i-confirm")]
    md = (d / CS.TEP_KQ_MD).read_text(encoding="utf-8")
    assert "Chờ thống kê viên làm tay" in md and "chưa có RCS" in md


def test_chay_tu_choi_chua_duyet_va_chua_khoa(tmp_path, monkeypatch):
    d = _de_tai(tmp_path)
    _dac_ta(d, duyet=False)
    _vao_tien_trinh(monkeypatch, tmp_path, d)
    with contextlib.redirect_stderr(io.StringIO()):
        assert CS.main(["chay", "--study", "SAP"]) == 3
    _dac_ta(d)
    (d / "DATA_LOCK_manifest.json").unlink()
    with contextlib.redirect_stderr(io.StringIO()):
        assert CS.main(["chay", "--study", "SAP"]) == 3
    assert not (d / CS.TEP_KQ_JSON).exists()


# ───────────────────────── --loc trong run_stats ─────────────────────────


def _main_loc(goc: Path, monkeypatch, loc: str) -> tuple[Path, str]:
    d = goc / "exports" / "SAP"
    _vao_tien_trinh(monkeypatch, goc, d)
    monkeypatch.setattr(sys, "argv", ["run_stats_analysis.py", "--data", str(d / "05_clean_locked" / "k.csv"),
                                      "--study", "SAP", "--gate", "G6", "--outcome", "g1", "--group", "nhom",
                                      "--outcome-type", "ordinal", "--n-imputations", "2", "--loc", loc])  # fmt: skip
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        RSA.main()
    return d, out.getvalue()


def test_loc_quan_the_va_ghi_dac_ta(tmp_path, monkeypatch):
    _de_tai(tmp_path)
    d, ra = _main_loc(tmp_path, monkeypatch, "hop_le == 1 and mode == 1")
    tom = json.loads((d / "G6_analysis_summary.json").read_text(encoding="utf-8"))
    df = pd.read_csv(d / "05_clean_locked" / "k.csv")
    ky = int((df.g1.notna() & (df["mode"] == 1)).sum())
    assert tom["loc"] == {"bieu_thuc": "hop_le == 1 and mode == 1", "n_truoc": 300, "n_sau": ky}
    assert tom["n_total"] == ky and tom["dac_ta_phan_tich"]["loc"] == "hop_le == 1 and mode == 1"
    assert set(tom["bien_phai_sinh"]["bien"]) == {"hop_le"}  # biến phái sinh của biểu thức lọc được tính + ghi


@pytest.mark.parametrize("loc", ["1 < g1 < 3", "khong_co == 1", "mode == 9"])
def test_loc_sai_thi_dung(tmp_path, monkeypatch, loc):
    _de_tai(tmp_path)
    with pytest.raises(SystemExit) as e:
        _main_loc(tmp_path, monkeypatch, loc)
    assert e.value.code == 1


def test_loc_dung_bien_phai_sinh_chua_duyet_thi_dung(tmp_path, monkeypatch):
    _de_tai(tmp_path, duyet_ps=False)
    with pytest.raises(SystemExit):
        _main_loc(tmp_path, monkeypatch, "hop_le == 1")


# ───────────────────────── cầu nối: lọc, gate, phơi nhiễm liên tục ─────────────────────────


def test_khoi_loc_spss_r_cung_bieu_thuc(tmp_path):
    tom = {"dac_ta_phan_tich": {"loc": 'hop_le == 1 and d < ngay("2026-07-01")', "loc_cot_ngay": ["d"]},
           "bien_phai_sinh": {"bien": {"hop_le": {}}}}  # fmt: skip
    sp = B.khoi_loc_cau_noi(tom, "spss", ten_spss={"d": ("NGAY", False)})
    assert "NUMBER(NGAY, SDATE10)" in sp and "SELECT IF (ebm_loc = 1)." in sp and "hop_le" in sp
    assert sp.index("SELECT IF") > sp.index("COMPUTE ebm_loc")
    r = B.khoi_loc_cau_noi(tom, "r", bien_d="D")
    assert 'D <- D[!is.na(.loc) & .loc == 1, , drop = FALSE]' in r and '.bps_ngay(D[["d"]])' in r
    assert B.khoi_loc_cau_noi({"dac_ta_phan_tich": {}}, "spss") == ""


def test_spss_cu_phap_loc_giua_phai_sinh_va_bien_gia(tmp_path, monkeypatch):
    goc = tmp_path
    _de_tai(goc)
    d, _ra = _main_loc(goc, monkeypatch, "hop_le == 1")
    man = {"sav": str(d / "x.sav"), "nguon_csv": str(d / "05_clean_locked" / "k.csv"),
           "bien": [{"cot": c, "ten": c, "so": True, "bo": False, "muc": None, "nhan": c, "nhan_gia_tri": {},
                     "ma_chu": {}} for c in ("cho", "kg", "mode", "g1", "nhom")]}  # fmt: skip
    man = S.them_loc("SAP", S.them_bien_phai_sinh("SAP", man, "G6"), "G6")
    dt = {"outcome": "g1", "group": "nhom", "covariates": ["kg"], "covariates_mo_hinh": ["kg_2", "kg_3"],
          "outcome_type": "ordinal", "time": None, "event": None, "cot_cum": None, "don_vi_phoi_nhiem": None,
          "hiep_bien_phan_loai": {"kg": {"tham_chieu": "1", "muc": ["2", "3"], "ten": ["kg_2", "kg_3"]}}}  # fmt: skip
    man = S.them_bien_gia(man, dt)
    vb, _cb, _phu = S.cu_phap_phan_tich("SAP", man, dt, tmp_path / "kq")
    assert vb.index("COMPUTE hop_le") < vb.index("SELECT IF (ebm_loc = 1).") < vb.index("COMPUTE kg_2")


def test_kiem_cheo_ten_tep_theo_gate_va_mo_ta_khong_ap_dung(tmp_path, monkeypatch):
    assert KC.tep_kiem_cheo("G6") == ("G6_kiem_cheo.json", "G6_kiem_cheo.md")
    assert KC.tep_kiem_cheo("G6_dn") == ("G6_dn_kiem_cheo.json", "G6_dn_kiem_cheo.md")
    monkeypatch.setattr(KC, "thu_muc_de_tai", lambda s: tmp_path)
    (tmp_path / "G6_ty_analysis_summary.json").write_text(json.dumps({"dac_ta_phan_tich": {"outcome": None}}),
                                                          encoding="utf-8", newline="\n")  # fmt: skip
    with contextlib.redirect_stdout(io.StringIO()):
        assert KC.main(["chay", "--study", "X", "--gate", "G6_ty"]) == 0
    kq = json.loads((tmp_path / "G6_ty_kiem_cheo.json").read_text(encoding="utf-8"))
    assert kq["trang_thai"] == KC.KHONG_AP_DUNG and "chỉ mô tả" in kq["ly_do"]
    assert not (tmp_path / "G6_kiem_cheo.json").exists()  # không ghi đè tệp của gate G6


def test_phoi_nhiem_lien_tuc_bo_so_tho_o_ca_ba(tmp_path, monkeypatch):
    _de_tai(tmp_path)
    d = tmp_path / "exports" / "SAP"
    _vao_tien_trinh(monkeypatch, tmp_path, d)
    monkeypatch.setattr(sys, "argv", ["run_stats_analysis.py", "--data", str(d / "05_clean_locked" / "k.csv"),
                                      "--study", "SAP", "--gate", "G6", "--outcome", "nhom", "--group", "cho",
                                      "--outcome-type", "binary", "--n-imputations", "2"])  # fmt: skip
    with contextlib.redirect_stdout(io.StringIO()):
        RSA.main()
    tom = json.loads((d / "G6_analysis_summary.json").read_text(encoding="utf-8"))
    assert tom["primary_outcome"]["skipped"] is True and "error" not in tom["primary_outcome"]
    man = {"sav": "x.sav", "bien": [{"cot": "nhom", "ten": "nhom", "so": True, "muc": ["0", "1"]},
                                    {"cot": "cho", "ten": "cho", "so": True, "muc": None}]}  # fmt: skip
    dt = {"outcome": "nhom", "group": "cho", "covariates": [], "outcome_type": "binary", "time": None, "event": None,
          "cot_cum": None, "don_vi_phoi_nhiem": None}  # fmt: skip
    vb, cb, _phu = S.cu_phap_phan_tich("SAP", man, dt, tmp_path / "kq")
    assert "CROSSTABS /TABLES=cho" not in vb and any("bỏ so sánh thô" in x for x in cb)
    assert R._ket_cuc_chinh(tom, {}, {}) == []
    vr = R.sinh_script_r("SAP", tmp_path / "k.csv", "ab" * 32, tmp_path / "r.json", dt, "binary", None)
    assert "if (HAI_NHOM) KET$ket_cuc_chinh" in vr and "co(CUM) && HAI_NHOM" in vr


def test_r_tham_chieu_khoi_bo_sung_co_phai_sinh_loc_bien_gia(tmp_path, monkeypatch):
    _de_tai(tmp_path)
    d, _ra = _main_loc(tmp_path, monkeypatch, "hop_le == 1")
    man = {"nguon_csv": str(d / "05_clean_locked" / "k.csv"), "bien": []}
    dt = {"hiep_bien_phan_loai": {"kg": {"tham_chieu": "1", "muc": ["2", "3"], "ten": ["kg_2", "kg_3"]}}}
    ma = S.ma_r_chuan_bi_tham_chieu("SAP", "G6", man, dt)
    assert ma.index('d[["hop_le"]] <-') < ma.index("d <- d[!is.na(.loc)") < ma.index('d[["kg_2"]] <-')
    assert "# @@KHOI_CHUAN_BI@@" in S.R_DOI_CHIEU


def test_r_tham_chieu_ghi_khoi_chuan_bi_vao_script(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "tim_rscript", lambda: "Rscript")
    monkeypatch.setattr(S, "_chay_lenh", lambda *a, **k: (0, "", ""))
    man = {"bien": [{"cot": "y", "ten": "y"}]}
    dt = {"hon_hop_da_sinh": True, "cot_cum": "ban", "outcome": "y", "group": "g", "covariates": ["kg"],
          "covariates_mo_hinh": ["kg_2"], "outcome_type": "ordinal"}  # fmt: skip
    S.chay_r_tham_chieu(man, dt, tmp_path / "x.sav", tmp_path, his=None, khoi_r="d[['kg_2']] <- 1\n")
    vb = (tmp_path / "r_doi_chieu.R").read_text(encoding="utf-8")
    assert "d[['kg_2']] <- 1" in vb and "@@KHOI_CHUAN_BI@@" not in vb
    assert json.loads((tmp_path / "r_tham_so.json").read_text(encoding="utf-8"))["covariates"] == ["kg_2"]


def test_r_cu_phap_chen_khoi_loc(tmp_path, monkeypatch):
    _de_tai(tmp_path)
    d, _ra = _main_loc(tmp_path, monkeypatch, "hop_le == 1")
    with contextlib.redirect_stdout(io.StringIO()):
        assert R.main(["cu-phap", "--study", "SAP"]) == R.MA_OK
    vb = (d / "r" / "SAP_phan_tich.R").read_text(encoding="utf-8")
    assert vb.index('D[["hop_le"]] <-') < vb.index("D <- D[!is.na(.loc) & .loc == 1, , drop = FALSE]") < vb.index(
        "KET <- list()")
