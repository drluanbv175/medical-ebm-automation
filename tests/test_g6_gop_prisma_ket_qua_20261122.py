# -*- coding: utf-8 -*-
"""G6 gộp ra ĐỦ số cho các mục kết quả PRISMA 2020 (17, 19, 20c, 21) và G7 chép nguyên văn (22/11/2026).

Đo trên giả lập `ZZCANARY-TONG-QUAN-GOP` (k = 15): SAP §5 khoá «biểu đồ phễu + kiểm định Egger khi ≥ 10 nghiên cứu»
nhưng tóm tắt G6 không có Egger (mục 21); SAP §7 khoá «Nhóm nhỏ tiền định: Loại thuốc SGLT2» nhưng đặc tả G6 để «làm
tay» (20c); `tung_nghien_cuu` chỉ có log RR/var, không có biến cố/số người từng nhánh (19); Bảng 1 của G7 là «Đặc điểm
nền người tham gia» trung bình gộp, không phải đặc điểm TỪNG nghiên cứu (17); GRADE chưa có khung (22 — phán đoán của
người, máy không xếp mức).

Giá trị tham chiếu tính ĐỘC LẬP bằng metafor 5.0.1 (escalc RR + rma DL; regtest(model = "lm", predictor = "sei");
phân nhóm = rma DL từng tập con rồi rma(yi = μ_g, sei = se_g, method = "FE")$QE) trên dữ liệu 15 thử nghiệm của giả lập.
Test chạy R thật bị bỏ qua khi máy không có Rscript + metafor. Thư mục tạm, dữ liệu mô phỏng, không mạng.
Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "tools", ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import bieu_do_gop as GP  # noqa: E402
import chay_sap_g6 as CS6  # noqa: E402
import kiem_chuan_de_cuong_theo_muc as K  # noqa: E402
import phan_tich_thiet_ke_dac_thu as P  # noqa: E402
import run_g7_auto as G7  # noqa: E402

# 15 thử nghiệm của giả lập ZZCANARY-TONG-QUAN-GOP (dữ liệu mô phỏng)
_G = (2, 1, 2, 2, 4, 3, 4, 1, 3, 2, 1, 4, 2, 1, 1)
_A = (77, 78, 56, 112, 29, 66, 32, 57, 47, 55, 56, 89, 80, 138, 29)
_N1 = (3264, 2375, 1445, 3556, 2239, 3462, 1081, 1814, 3668, 2032, 2144, 3186, 4443, 4189, 989)
_C = (110, 120, 70, 162, 48, 107, 42, 83, 74, 82, 77, 119, 108, 204, 41)
_N0 = (3217, 2419, 1464, 3549, 2258, 3488, 1083, 1794, 3701, 2056, 2136, 3205, 4416, 4142, 1030)
HANG = [{"s": f"TN{i + 1:02d}", "g": g, "a": a, "n1": n1, "c": c, "n0": n0}
        for i, (g, a, n1, c, n0) in enumerate(zip(_G, _A, _N1, _C, _N0))]
TS = {"nhan_nghien_cuu": "s", "su_kien_can_thiep": "a", "n_can_thiep": "n1", "su_kien_chung": "c", "n_chung": "n0"}
NHAN = {"1": "Empagliflozin", "2": "Dapagliflozin", "3": "Canagliflozin", "4": "Ertugliflozin"}
# metafor 5.0.1 (xem docstring)
R_EGGER = {"t": 0.427780928797817, "p": 0.675811899179226, "b": 0.236542136304167}
R_RD1000 = -11.1084556541898
R_NHOM = {"1": 0.682328619558686, "2": 0.713634152773111, "3": 0.629358624228049, "4": 0.722753469493008}
R_Q, R_P = 1.06761679992101, 0.784896699973115
R_NHOM_MOT_NC = {"1": 0.682328619558686, "2": 0.719827556213026, "3": 0.629358624228049, "4": 0.722753469493008,
                 "9": 0.689920343137255}
R_Q_MOT_NC, R_P_MOT_NC = 1.13444028509898, 0.888770081934787


def _gan(x: float, y: float, tol: float = 1e-9) -> bool:
    return abs(x - y) <= tol * max(1.0, abs(y))


def _gop(hang=HANG, phan_nhom=None, nhan=None) -> dict:
    return P.gop(hang, "s", "a", "n1", "c", "n0", phan_nhom, nhan)


# ═══════════════════════════════════════════ G6 — engine gộp ═══════════════════════════════════════════
def test_egger_khop_metafor_regtest_va_trung_hinh_pheu():
    kq = _gop()
    eg = kq["egger"]
    assert eg["da_chay"] is True and eg["k"] == 15 and eg["df"] == 13 and eg["nguong_k"] == 10
    assert _gan(eg["t"], R_EGGER["t"]) and _gan(eg["p"], R_EGGER["p"]) and _gan(eg["he_so_bat_doi_xung"], R_EGGER["b"])
    hinh = GP.egger([t["log_rr"] for t in kq["tung_nghien_cuu"]], [t["var"] for t in kq["tung_nghien_cuu"]])
    assert _gan(eg["t"], hinh["t"]) and _gan(eg["p"], hinh["p"])  # chữ trong bài = số trên biểu đồ phễu


def test_egger_duoi_10_nghien_cuu_khong_chay_va_khong_so_cheo():
    kq = _gop(HANG[:9])
    assert kq["egger"]["da_chay"] is False and "k = 9 < 10" in kq["egger"]["ly_do"]
    assert not {"egger_t", "egger_p"} & set(P.cac_so_doi_chieu("gop", kq))
    assert _gop(HANG[:10])["egger"]["da_chay"] is True  # đúng ngưỡng ≥ 10 của SAP


def test_phan_nhom_khop_metafor_thu_tu_ma_va_nhan_tu_dien():
    pn = _gop(phan_nhom="g", nhan=NHAN)["phan_nhom"]
    assert [g["ma"] for g in pn["nhom"]] == ["1", "2", "3", "4"] and pn["nhom"][1]["nhan"] == "Dapagliflozin"
    for g in pn["nhom"]:
        assert _gan(g["rr"], R_NHOM[g["ma"]]), g
    assert [g["k"] for g in pn["nhom"]] == [5, 5, 2, 3]
    assert _gan(pn["q_giua_nhom"], R_Q) and _gan(pn["p_giua_nhom"], R_P) and pn["df_giua_nhom"] == 3
    assert pn["nhom"][2]["nghien_cuu"] == ["TN06", "TN09"]


def test_phan_nhom_mot_nghien_cuu_van_vao_kiem_dinh_khac_biet():
    hang = [dict(r, g=9) if r["s"] == "TN01" else r for r in HANG]
    pn = _gop(hang, "g")["phan_nhom"]
    assert {g["ma"]: g["k"] for g in pn["nhom"]}["9"] == 1
    for g in pn["nhom"]:
        assert _gan(g["rr"], R_NHOM_MOT_NC[g["ma"]]), g
    assert _gan(pn["q_giua_nhom"], R_Q_MOT_NC) and _gan(pn["p_giua_nhom"], R_P_MOT_NC) and pn["df_giua_nhom"] == 4
    assert pn["nhom"][-1]["tau2"] == 0.0 and abs(pn["nhom"][-1]["q"]) < 1e-20  # k = 1 ⇒ τ² = 0, Q = 0 như metafor


def test_mot_phan_nhom_duy_nhat_khong_kiem_dinh():
    pn = _gop([dict(r, g=1) for r in HANG], "g")["phan_nhom"]
    assert pn["so_nhom"] == 1 and "q_giua_nhom" not in pn and "chỉ có một phân nhóm" in pn["ly_do"]


def test_so_bien_co_tung_nhanh_tong_va_hieu_ung_tuyet_doi():
    kq = _gop()
    t0 = kq["tung_nghien_cuu"][0]
    assert (t0["su_kien_can_thiep"], t0["n_can_thiep"], t0["su_kien_chung"], t0["n_chung"]) == (77, 3264, 110, 3217)
    assert all(isinstance(t["su_kien_can_thiep"], int) for t in kq["tung_nghien_cuu"])  # «77», không «77.0»
    assert not any(t["hieu_chinh_o_0"] for t in kq["tung_nghien_cuu"])
    assert kq["tong"] == {"su_kien_can_thiep": sum(_A), "n_can_thiep": sum(_N1), "su_kien_chung": sum(_C),
                          "n_chung": sum(_N0), "nguoi": sum(_N1) + sum(_N0)}
    hu = kq["hieu_ung_tuyet_doi"]
    ncc = sum(_C) / sum(_N0)
    assert _gan(hu["nguy_co_nhom_chung"], ncc) and _gan(hu["hieu_so_moi_1000"], R_RD1000)
    lo, hi = kq["ci_95"]
    assert _gan(hu["ci_95_hieu_so_moi_1000"][0], 1000 * ncc * (lo - 1))
    assert _gan(hu["ci_95_hieu_so_moi_1000"][1], 1000 * ncc * (hi - 1))
    assert _gan(hu["bien_co_can_thiep_moi_1000"], 1000 * ncc * kq["rr_gop_ngau_nhien"])
    o0 = _gop([{"s": "X", "a": 0, "n1": 40, "c": 3, "n0": 40}, *HANG[:2]])["tung_nghien_cuu"][0]
    assert o0["hieu_chinh_o_0"] is True and o0["su_kien_can_thiep"] == 0  # số chép nguyên, ô 0 ghi rõ


def test_dai_luong_doi_chieu_r_du_spss_bo_phan_nhom():
    py = P.cac_so_doi_chieu("gop", _gop(phan_nhom="g"))
    assert {"egger_t", "egger_p", "nguy_co_chung", "hieu_so_1000", "q_giua_nhom", "p_giua_nhom",
            "rr_nhom_1", "rr_nhom_4"} <= set(py)
    sp = P.dai_luong_spss("gop", py)
    assert "egger_p" in sp and "rr_gop" in sp and not [k for k in sp if k.startswith(("rr_nhom_", "q_giua", "p_giua"))]
    assert P.dai_luong_spss("du_bao", {"c_statistic": 1}) == ["c_statistic", "brier"]
    assert P.dai_luong_spss("chan_doan", {"auc": 1}) is None


def test_kich_ban_r_spss_co_egger_phan_nhom():
    ts = dict(TS, phan_nhom="g")
    r = P.kich_ban_r("gop", ts, Path("/tmp/dl.csv"), Path("/tmp/kq.txt"))
    assert 'metafor::regtest(m, model = "lm", predictor = "sei")' in r and f"nrow(es) >= {P.EGGER_K_TOI_THIEU}" in r
    assert 'paste0("rr_nhom_", lv)' in r and 'method = "FE"' in r and 'ghi("q_giua_nhom", mb$QE)' in r
    assert "rr_nhom_" not in P.kich_ban_r("gop", TS, Path("/tmp/dl.csv"), Path("/tmp/kq.txt"))
    sps = P.kich_ban_spss("gop", ts, Path("/tmp/dl.csv"), Path("/tmp/kq.csv"))
    assert "COMPUTE egger_t = b1 / SQRT(rss / (k - 2) * sw / dd)." in sps and "CDF.T(ABS(egger_t), k - 2)" in sps
    assert "/KEEP=rr_gop ci_duoi ci_tren tau2 i2 nguy_co_chung hieu_so_1000 egger_t egger_p." in sps
    assert ("g", "A60") in P._gia_tri_spss("gop", ts) and ("g", "A60") not in P._gia_tri_spss("gop", TS)


def _co_r_metafor() -> bool:
    if not shutil.which("Rscript"):
        return False
    r = subprocess.run(["Rscript", "-e", "cat(requireNamespace('metafor', quietly = TRUE))"], capture_output=True,
                       text=True, check=False)
    return r.stdout.strip().endswith("TRUE")


@pytest.mark.skipif(not _co_r_metafor(), reason="máy không có Rscript + metafor")
def test_kich_ban_r_that_khop_python_tung_dai_luong(tmp_path):
    """Kiểm chéo THẬT: chạy đúng kịch bản R sinh ra trên dữ liệu đã trích, so mọi đại lượng (cả phân nhóm, Egger)."""
    ts = dict(TS, phan_nhom="g")
    csv_p, ra = tmp_path / "dl.csv", tmp_path / "kq.txt"
    cot = [b for b, _ in P._gia_tri_spss("gop", ts)]
    csv_p.write_text(",".join(cot) + "\n" + "".join(",".join(str(r[c]) for c in cot) + "\n" for r in HANG),
                     encoding="utf-8", newline="\n")
    (tmp_path / "kb.R").write_text(P.kich_ban_r("gop", ts, csv_p, ra), encoding="utf-8", newline="\n")
    subprocess.run(["Rscript", str(tmp_path / "kb.R")], capture_output=True, text=True, check=True, timeout=300)
    py = P.cac_so_doi_chieu("gop", _gop(phan_nhom="g"))
    kq = P.so_khop(py, P._doc_kq_r(ra))
    assert kq["trang_thai"] == "KHOP" and kq["so_dai_luong"] == 15, kq


# ─────────────────────────────────── bảng đặc điểm từng nghiên cứu (PRISMA 17) ───────────────────────────────────
_TU_DIEN = ("Variable / Field Name,Form Name,Section Header,Field Type,Field Label,\"Choices, Calculations, OR Slider "
            "Labels\"\n"
            "s,phieu,,text,Mã thử nghiệm (tác giả–năm),\n"
            "g,phieu,,dropdown,Thuốc ức chế SGLT2,\"1, Empagliflozin | 2, Dapagliflozin | 3, Canagliflozin | 4, "
            "Ertugliflozin\"\n"
            "a,phieu,,text,Biến cố nhánh SGLT2,\n"
            "n1,phieu,,text,Số người nhánh SGLT2,\n"
            "c,phieu,,text,Biến cố nhánh chứng,\n"
            "n0,phieu,,text,Số người nhánh chứng,\n"
            "tg,phieu,,text,Thời gian theo dõi (tháng),\n"
            "rob,phieu,,radio,RoB 2 — đánh giá chung,\"1, Thấp | 2, Có lo ngại | 3, Cao\"\n")


def _df_gop():
    import pandas as pd

    df = pd.DataFrame(HANG)
    return df.assign(tg=[40.3, 39.8, 44.4, 29.7, 47.6, 24.7, 32.4, 37.8, 46.6, 38.2, 48.4, 44.1, 43.2, 24.2, 35.5],
                     rob=[1, 1, 2, 2, 1, 1, 1, 2, 1, 2, 1, 1, 1, 1, 2])


@pytest.fixture
def de_tai_gop(tmp_path, monkeypatch):
    d = tmp_path / "exports" / "GOP"
    d.mkdir(parents=True)
    (d / "G5_REDCap_dictionary_GOP.csv").write_text(_TU_DIEN, encoding="utf-8", newline="\n")
    monkeypatch.setattr(P, "thu_muc_de_tai", lambda study: d)
    monkeypatch.setattr(P, "_doc_df_khoa", lambda study, can, loc=None: (_df_gop(), d / "khoa.csv", {}))
    return d


def test_bang_dac_diem_tung_nghien_cuu_nhan_tu_dien_bo_bien_co(de_tai_gop):
    bd = P.bang_dac_diem_nghien_cuu("GOP", dict(TS, phan_nhom="g"), [r["s"] for r in HANG if r["s"] != "TN15"])
    assert [c["bien"] for c in bd["cot"]] == ["g", "n1", "n0", "tg", "rob"]  # bỏ nhãn NC và số biến cố hai nhánh
    assert bd["cot"][0]["nhan"] == "Thuốc ức chế SGLT2"
    assert bd["nhan_nghien_cuu"]["nhan"] == "Mã thử nghiệm (tác giả–năm)"
    assert bd["k"] == 14 and "TN15" not in [x["nghien_cuu"] for x in bd["dong"]]  # chỉ nghiên cứu ĐÃ vào phân tích
    assert bd["dong"][0]["gia_tri"] == {"g": "Dapagliflozin", "n1": 3264, "n0": 3217, "tg": 40.3, "rob": "Thấp"}
    assert isinstance(bd["dong"][0]["gia_tri"]["n1"], int)


def test_bang_dac_diem_loi_doc_khoa_tra_error(de_tai_gop, monkeypatch):
    def hong(*_a, **_k):
        raise P.TuChoi("chưa khoá")

    monkeypatch.setattr(P, "_doc_df_khoa", hong)
    assert "chưa khoá" in P.bang_dac_diem_nghien_cuu("GOP", TS, ["TN01"])["error"]


def test_chay_gop_ghi_tom_tat_du_so_qua_tep_tam(de_tai_gop, monkeypatch):
    import cau_noi_spss as S

    monkeypatch.setattr(P, "_g4_da_khoa", lambda study: None)
    monkeypatch.setattr(S, "tim_du_lieu_khoa", lambda study: (de_tai_gop / "khoa.csv", {"sha256": "ab" * 32}))
    assert P.chay("GOP", "G6_NC", "gop", dict(TS, phan_nhom="g"), False) == 0
    tom = json.loads((de_tai_gop / "G6_NC_analysis_summary.json").read_text(encoding="utf-8"))
    dt = tom["dac_thu"]
    assert dt["egger"]["da_chay"] and dt["phan_nhom"]["nhom"][0]["nhan"] == "Empagliflozin"
    assert _gan(dt["phan_nhom"]["q_giua_nhom"], R_Q) and dt["tung_nghien_cuu"][0]["n_can_thiep"] == 3264
    assert tom["bang_dac_diem_nghien_cuu"]["k"] == 15 and tom["dac_ta_phan_tich"]["phan_nhom"] == "g"
    md = (de_tai_gop / "G6_NC_ket_qua.md").read_text(encoding="utf-8")
    assert "| TN01 | 77/3264 | 110/3217 |" in md and "Kiểm định Egger (k = 15)" in md
    assert "Khác biệt giữa phân nhóm" in md
    assert not list(de_tai_gop.glob(".*.tam"))


# ─────────────────────────────────── đặc tả SAP G6 (chay_sap_g6) ───────────────────────────────────
def _dac_ta(d: Path, phan_tich: list) -> dict:
    sap = d / "SAP.md"
    sap.write_text("# SAP\n### §4 PHÂN TÍCH CHÍNH\n- **Phương pháp:** gộp\n", encoding="utf-8", newline="\n")
    return {"nguon_sap": sap.name, "sha256_sap": hashlib.sha256(sap.read_bytes()).hexdigest(), "phan_tich": phan_tich}


def test_dac_ta_nhan_phan_nhom_cho_gop_chan_cho_loai_khac(tmp_path):
    gop = {"id": "MT1", "vai": "chinh", "sap_muc": "§4", "mo_ta": "gộp", "tham_so": {"loai_dac_thu": "gop", **TS}}
    nc = {"id": "NC", "vai": "nhom_con", "sap_muc": "§7", "mo_ta": "phân nhóm",
          "tham_so": {"loai_dac_thu": "gop", **TS, "phan_nhom": "g"}}
    db = {"id": "DB", "vai": "phu", "sap_muc": "§8", "mo_ta": "dự báo",
          "tham_so": {"loai_dac_thu": "du_bao", "outcome": "y", "covariates": ["x"], "phan_nhom": "g"}}
    loi = CS6.kiem_dac_ta(tmp_path, _dac_ta(tmp_path, [gop, nc, db]))["loi"]
    assert not [x for x in loi if x.startswith("NC:")], loi
    assert any(x.startswith("DB:") and "phan_nhom" in x for x in loi), loi
    assert CS6.doi_so_run_stats(nc)[-2:] == ["--phan-nhom", "g"]
    assert CS6._kiem_gia_tri("phan_nhom", CS6.THAM_SO["phan_nhom"][1], "-x") != []


def test_chi_muc_tom_tat_egger_va_q_giua_nhom():
    tom = {"n_total": 15, "loai_dac_thu": "gop", "dac_thu": _gop(phan_nhom="g")}
    g = CS6._tom_tat_uoc_luong(tom)["gop"]
    assert _gan(g["egger_p"], R_EGGER["p"]) and _gan(g["q_giua_nhom"], R_Q) and g["phan_nhom"] == "g"
    assert "egger_p" not in CS6._tom_tat_uoc_luong({"n_total": 9, "loai_dac_thu": "gop",
                                                    "dac_thu": _gop(HANG[:9])})["gop"]


def test_kich_ban_gia_lap_tong_quan_chay_phan_nhom_thuoc():
    import gia_lap_kich_ban_them as KB

    g6 = KB.sap_g6_tron_vong()["tong_quan_gop"]["g6"]
    nc = next(x for x in g6 if x["id"] == "NC_thuoc")
    assert nc.get("ke_thua") and nc["tham_so"] == {"phan_nhom": "thuoc_sglt2"} and "chua_tu_dong" not in nc


# ─────────────────────────────────── hình (bieu_do_gop / hinh_g6) ───────────────────────────────────
def _ds(hang, nhom_cua=lambda r: str(r["g"])):
    ra = []
    for r in hang:
        yi, vi = P._o_rr(r["a"], r["n1"], r["c"], r["n0"])
        ra.append({"nghien_cuu": r["s"], "nhom": nhom_cua(r), "yi": yi, "vi": vi, "sei": math.sqrt(vi)})
    return ra


def test_forest_phan_nhom_mot_nghien_cuu_van_vao_kiem_dinh_trung_g6(tmp_path):
    hang = [dict(r, g=9) if r["s"] == "TN01" else r for r in HANG]
    sl = GP.ve_forest(_ds(hang), "RR", tmp_path / "f", "DL")
    assert sl["kiem_dinh_khac_biet_nhom"]["df"] == 4 and "9" not in sl["phan_nhom"]  # kim cương chỉ khi ≥ 2 NC
    assert _gan(sl["kiem_dinh_khac_biet_nhom"]["Q"], R_Q_MOT_NC, 1e-8)


def test_hinh_g6_phan_nhom_ve_forest_theo_nhom_khong_lap_pheu(tmp_path):
    import hinh_g6 as HG
    import pandas as pd

    df = pd.DataFrame(HANG)
    pt = [{"id": "NC", "vai": "nhom_con", "tham_so": {"loai_dac_thu": "gop", **TS, "phan_nhom": "g"}}]
    HG.sinh("x", tmp_path, pt, None, None, nap=lambda s, c, loc: df.copy())
    tep = sorted(p.name for p in (tmp_path / "bieu-bang").glob("g6-nc-*.png"))
    assert tep == ["g6-nc-forest-phan-nhom.png"], tep
    j = json.loads((tmp_path / "bieu-bang/g6-nc-forest-phan-nhom.json").read_text(encoding="utf-8"))
    assert set(j["phan_nhom"]) == {"1", "2", "3", "4"} and _gan(j["kiem_dinh_khac_biet_nhom"]["Q"], R_Q, 1e-8)
    assert list(j["phan_nhom"]) == ["1", "2", "3", "4"]  # thứ tự theo mã như bảng §3b (dữ liệu bắt đầu bằng mã 2)


def test_hinh_g6_pheu_cung_nguong_egger_cua_g6(tmp_path):
    import hinh_g6 as HG
    import pandas as pd

    pt = [{"id": "GOP", "vai": "chinh", "tham_so": {"loai_dac_thu": "gop", **TS}}]
    HG.sinh("x", tmp_path / "a", pt, None, None, nap=lambda s, c, loc: pd.DataFrame(HANG[:10]).copy())
    HG.sinh("x", tmp_path / "b", pt, None, None, nap=lambda s, c, loc: pd.DataFrame(HANG[:9]).copy())
    assert (tmp_path / "a/bieu-bang/g6-gop-pheu.png").is_file()  # k = 10: G6 chạy Egger ⇒ có phễu
    assert not (tmp_path / "b/bieu-bang/g6-gop-pheu.png").exists()  # k = 9: không Egger, không phễu


# ═══════════════════════════════════════════ G7 — chép nguyên văn ═══════════════════════════════════════════
SHA = "ab" * 32


def _tom_tat(dac_thu: dict, **them) -> dict:
    return {"gate": "G6", "study": "THU", "loai_dac_thu": "gop", "n_total": 15, "dac_thu": dac_thu,
            "dac_ta_phan_tich": {"loai_dac_thu": "gop", **TS}, "generated": datetime.now().isoformat(),
            "data_lock": {"sha256": SHA}, **them}


def _vb(tt: dict) -> str:
    return json.dumps(tt, ensure_ascii=False, indent=1)


def test_g7_khoi_gop_chep_bien_co_tung_nhanh_egger_tuyet_doi_nguyen_van():
    tt = json.loads(_vb(_tom_tat(_gop())))
    khoi = G7._khoi_dac_thu_g6("gop", tt["dac_thu"], "G6_analysis_summary.json")
    text = "\n".join(khoi)
    t0 = tt["dac_thu"]["tung_nghien_cuu"][0]
    assert f"| TN01 | {t0['rr']!r} | {t0['ci_95'][0]!r}–{t0['ci_95'][1]!r} | 77/3264 | 110/3217 |" in text
    eg = tt["dac_thu"]["egger"]
    assert f"t = {eg['t']!r}, df = 13, p = {eg['p']!r}" in text and "Sai lệch công bố — kiểm định Egger" in text
    assert f"{sum(_N1) + sum(_N0)} người" in text and "Hiệu ứng tuyệt đối" in text
    assert G7.kiem_so_trich_g6(text, _vb(tt)) == []  # không tính lại, không làm tròn
    assert "Phân nhóm theo" not in text  # phân tích chính không có phân nhóm


def test_g7_khoi_gop_tom_tat_cu_khong_them_cot_khong_them_o():
    cu = _gop()
    for t in cu["tung_nghien_cuu"]:
        del t["su_kien_can_thiep"]
    for k in ("egger", "tong", "hieu_ung_tuyet_doi"):
        cu.pop(k)
    text = "\n".join(G7._khoi_dac_thu_g6("gop", json.loads(json.dumps(cu)), "G6_analysis_summary.json"))
    assert "| Nghiên cứu | RR | 95% CI |\n|---|---|---|\n" in text and "Egger" not in text and "[CẦN T" not in text


def test_g7_khoi_egger_khong_chay_chep_ly_do_g6():
    eg = _gop(HANG[:9])["egger"]
    dong = G7._khoi_sai_lech_cong_bo_g6(eg)
    assert "kiểm định Egger không chạy (G6)" in dong[1] and "k = 9 < 10" in dong[1]


def test_g7_bang1_tong_quan_la_dac_diem_tung_nghien_cuu(de_tai_gop, tmp_path):
    from test_g7_tu_dien_ket_qua_g6_20261115 import _manifest, _sinh

    bd = P.bang_dac_diem_nghien_cuu("GOP", TS, [r["s"] for r in HANG])
    out = tmp_path / "exports" / "THU"
    _manifest(out)
    (out / "G6_analysis_summary.json").write_text(_vb(_tom_tat(_gop(), bang_dac_diem_nghien_cuu=bd)),
                                                  encoding="utf-8", newline="\n")
    kq = G7.dung_ket_qua_tu_g6(G7.doc_tom_tat_g6_hop_le(out))
    assert kq["da_dung"], kq.get("ly_do")
    assert kq["k_nghien_cuu"] == "15" and kq["bien_bang1"] == [] and kq["n_theo_nhom"] is None
    s2 = "\n".join(kq["s2"])
    assert ("| Mã thử nghiệm (tác giả–năm) | Thuốc ức chế SGLT2 | Số người nhánh SGLT2 | Số người nhánh chứng | "
            "Thời gian theo dõi (tháng) | RoB 2 — đánh giá chung |") in s2
    assert "| TN01 | Dapagliflozin | 3264 | 3217 | 40.3 | Thấp |" in s2
    text = _sinh(ket_qua_g6=kq, table1_shell="*ghi chú*", design_code="sr_ma", reporting_std="PRISMA 2020")
    assert "*Bảng 1. Đặc điểm các nghiên cứu được đưa vào tổng hợp (k = 15 — G6)*" in text
    assert "Đặc điểm nền người tham gia" not in text and "**§2 Đặc điểm các nghiên cứu — Bảng 1:**" in text


def test_g7_bang_dac_diem_loi_thanh_o_thong_ke_vien(tmp_path):
    from test_g7_tu_dien_ket_qua_g6_20261115 import _manifest

    out = tmp_path / "exports" / "THU"
    _manifest(out)
    (out / "G6_analysis_summary.json").write_text(
        _vb(_tom_tat(_gop(), bang_dac_diem_nghien_cuu={"error": "không dựng được"})), encoding="utf-8", newline="\n")
    kq = G7.dung_ket_qua_tu_g6(G7.doc_tom_tat_g6_hop_le(out))
    assert kq["s2"] == ["[CẦN THỐNG KÊ VIÊN — G6 báo lỗi bảng đặc điểm từng nghiên cứu: không dựng được]  "]
    assert kq["k_nghien_cuu"] is None


def test_g7_khung_tom_tat_phat_hien_khong_xep_muc_grade():
    tt = json.loads(_vb(_tom_tat(_gop())))
    kq6 = {"da_dung": True, "nguon": "G6_analysis_summary.json", "tom_tat_g6": tt, "van_ban_g6": _vb(tt)}
    dong = G7.khoi_tom_tat_phat_hien_g6(kq6, "HbA1c sau 12 tháng")  # tên kết cục có số: không vào tự kiểm
    text = "\n".join(dong)
    hang = next(x for x in dong if x.startswith("| HbA1c sau 12 tháng |"))
    assert f"| {15} ({sum(_N1) + sum(_N0)}) |" in hang and repr(tt["dac_thu"]["rr_gop_ngau_nhien"]) in hang
    assert "[CẦN XẾP MỨC CHẮC CHẮN GRADE" in hang and "Mức chắc chắn (GRADE)" in text
    assert "tác giả" not in hang.lower()  # bước điền của giả lập từng chép TÊN người vào ô có chữ «tác giả»
    import re
    assert not re.search(r"\b(cao|trung bình|thấp|rất thấp)\b", hang.split("[CẦN")[0])  # máy không xếp mức
    assert G7.khoi_tom_tat_phat_hien_g6({"da_dung": True, "tom_tat_g6": _tom_tat({"k": 2})}, "x") == []
    sai = json.loads(_vb(tt))
    sai["dac_thu"]["hieu_ung_tuyet_doi"]["hieu_so_moi_1000"] = -11.11  # số không có trong tệp G6 ⇒ không dựng
    assert G7.khoi_tom_tat_phat_hien_g6({"da_dung": True, "tom_tat_g6": sai, "van_ban_g6": _vb(tt)}, "x") == []


def _de_tai_phan_nhom(tmp_path, *, nc_trong_chi_muc=True, dac_ta_nc=None):
    from test_g7_tu_dien_ket_qua_g6_20261115 import _manifest

    out = tmp_path / "exports" / "THU"
    _manifest(out)
    sap = out / "G4_A5_SAP_FINAL_THU.md"
    sap.write_text("# SAP\n### §4 PHÂN TÍCH CHÍNH\n", encoding="utf-8", newline="\n")
    nc = dac_ta_nc or {"id": "NC_thuoc", "vai": "nhom_con", "sap_muc": "§7", "mo_ta": "Phân nhóm theo thuốc",
                       "tham_so": {"loai_dac_thu": "gop", **TS, "phan_nhom": "g"}}
    dt = {"nguon_sap": sap.name, "sha256_sap": hashlib.sha256(sap.read_bytes()).hexdigest(), "phan_tich": [
        {"id": "MT1", "vai": "chinh", "sap_muc": "§4", "mo_ta": "gộp", "tham_so": {"loai_dac_thu": "gop", **TS}}, nc]}
    (out / "G6_DAC_TA_SAP.json").write_text(json.dumps(dt, ensure_ascii=False), encoding="utf-8", newline="\n")
    tt = _tom_tat(_gop(phan_nhom="g", nhan=NHAN))
    (out / "G6_NC_thuoc_analysis_summary.json").write_text(_vb(tt), encoding="utf-8", newline="\n")
    pt = [{"id": "MT1", "vai": "chinh", "trang_thai": "DA_CHAY", "gate": "G6"}]
    if nc_trong_chi_muc:
        pt.append({"id": "NC_thuoc", "vai": "nhom_con", "sap_muc": "§7", "mo_ta": "Phân nhóm theo thuốc",
                   "trang_thai": "DA_CHAY", "gate": "G6_NC_thuoc", "uoc_luong": CS6._tom_tat_uoc_luong(tt)})
    (out / G7.TEP_SAP_KET_QUA_G6).write_text(json.dumps(
        {"study": "THU", "dac_ta": {"dau": CS6.kiem_dac_ta(out, dt)["dau"]},
         "du_lieu_khoa": {"tep": "x.csv", "sha256": SHA}, "phan_tich": pt}, ensure_ascii=False),
        encoding="utf-8", newline="\n")
    return out, tt


def test_g7_phan_nhom_tu_chi_muc_sap_chep_nguyen_van(tmp_path):
    out, tt = _de_tai_phan_nhom(tmp_path)
    dong = G7.dung_phan_nhom_g6(out)
    text = "\n".join(dong)
    pn = json.loads(_vb(tt))["dac_thu"]["phan_nhom"]
    assert dong[0] == "**§3b Phân nhóm tiền định (SAP):**  " and "**`NC_thuoc`** (SAP §7)" in text
    assert f"| Empagliflozin | 5 | {pn['nhom'][0]['rr']!r} |" in text
    assert f"Khác biệt giữa các phân nhóm: Q = {pn['q_giua_nhom']!r}, df = 3, p = {pn['p_giua_nhom']!r}" in text
    khoi = text.split("`G6_NC_thuoc_analysis_summary.json`, n = 15")[1]
    assert G7.kiem_so_trich_g6(khoi, _vb(tt)) == []
    assert "TN01" in text and "77/3264" not in text  # chỉ khối phân nhóm — không lặp bảng từng nghiên cứu


def test_g7_phan_nhom_vang_chi_muc_thanh_o_cho_khong_bien_mat(tmp_path):
    out, _ = _de_tai_phan_nhom(tmp_path, nc_trong_chi_muc=False)
    text = "\n".join(G7.dung_phan_nhom_g6(out))
    assert "**`NC_thuoc`** (SAP §7): [CẦN THỐNG KÊ VIÊN — SAP cam kết phân nhóm này nhưng" in text


def test_g7_phan_nhom_khong_ap_dung_khi_nhom_con_khong_phai_gop_phan_nhom(tmp_path):
    loc = {"id": "NC_nu", "vai": "nhom_con", "sap_muc": "§7", "mo_ta": "nữ",
           "tham_so": {"loai_dac_thu": "gop", **TS, "loc": "g == 1"}}
    out, _ = _de_tai_phan_nhom(tmp_path, nc_trong_chi_muc=False, dac_ta_nc=loc)
    assert G7.dung_phan_nhom_g6(out) is None
    assert G7.dung_ket_cuc_phu_g6(out) is None  # đường kết cục phụ không đổi


# ═══════════════════════════════════════════ vòng kín K18 ═══════════════════════════════════════════
def _ban_thao_k18(ket_qua: str) -> str:
    import test_k18_prisma_2020_20261122 as T18

    return T18._tq(ket_qua=ket_qua)


def _ket_qua_tu_bo_sinh(grade: str = "") -> str:
    tt = json.loads(_vb(_tom_tat(_gop())))
    s3 = G7._khoi_dac_thu_g6("gop", tt["dac_thu"], "G6_analysis_summary.json")
    pn = G7._khoi_phan_nhom_gop_g6(json.loads(json.dumps(_gop(phan_nhom="g", nhan=NHAN)["phan_nhom"])))
    sof = G7.khoi_tom_tat_phat_hien_g6({"da_dung": True, "nguon": "G6", "tom_tat_g6": tt, "van_ban_g6": _vb(tt)},
                                       "Nhập viện vì suy tim")
    md = "\n".join(["## 3. KẾT QUẢ", "", "*Bảng 1. Đặc điểm các nghiên cứu được đưa vào tổng hợp (k = 15 — G6)*", "",
                    *s3, *pn, "", *sof])
    md = md.replace(G7.NHAN_DOI_CHIEU_G6, "")  # bước tác giả đối chiếu xong gỡ nhãn
    dau = md.index("[CẦN XẾP MỨC CHẮC CHẮN")
    return md.replace(md[dau:md.index("]", dau) + 1], grade or "—")


def test_k18_khoi_bo_sinh_lam_muc_19_20c_21_dat_22_cho_nguoi_xep():
    kq = K.doi_chieu(_ban_thao_k18(_ket_qua_tu_bo_sinh()), "systematic_review", che_do="ban_thao", co_so_lieu=True)
    muc = {r.ma: r for r in kq["ket_qua"] if r.chuan == "PRISMA 2020"}
    for ma in ("19", "20b", "20c", "21"):
        assert muc[ma].trang_thai == "dat", (ma, muc[ma].thieu)
    assert "đặc điểm các nghiên cứu" not in muc["17"].thieu  # bảng đúng loại; trích dẫn tuỳ dữ liệu có TLTK
    assert muc["22"].trang_thai == "thieu"  # khung có, mức GRADE chưa xếp — máy không xếp
    kq2 = K.doi_chieu(_ban_thao_k18(_ket_qua_tu_bo_sinh("Trung bình (hạ một mức vì thiếu chính xác)")),
                      "systematic_review", che_do="ban_thao", co_so_lieu=True)
    assert {r.ma: r for r in kq2["ket_qua"] if r.chuan == "PRISMA 2020"}["22"].trang_thai == "dat"


def test_k18_nhap_con_o_cho_thi_muc_ket_qua_chua_do():
    tt = json.loads(_vb(_tom_tat(_gop())))
    md = "\n".join(["## 3. KẾT QUẢ", "", *G7._khoi_dac_thu_g6("gop", tt["dac_thu"], "G6")])
    kq = K.doi_chieu(_ban_thao_k18(md), "systematic_review", che_do="ban_thao")
    assert {r.ma: r for r in kq["ket_qua"] if r.chuan == "PRISMA 2020"}["21"].trang_thai == "chua_do"


def test_ghi_nguyen_tu_khong_de_lai_tep_tam(tmp_path):
    p = tmp_path / "a.json"
    P._ghi_nguyen_tu(p, "x\n")
    P._ghi_nguyen_tu(p, "y\n")
    assert p.read_bytes() == b"y\n" and not list(tmp_path.glob(".*"))
