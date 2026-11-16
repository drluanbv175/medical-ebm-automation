"""Phân tích ĐẶC THÙ cho chẩn đoán · dự báo · tổng quan–gộp · định tính (16/11/2026 — giả lập trọn vòng 8 thiết kế: bốn
thiết kế này qua G6 mà không có một con số nào vì run_stats_analysis chưa có đường).

Giá trị tham chiếu lấy ĐỘC LẬP từ R (metafor::rma method="DL"; pROC::auc) trên dữ liệu cố định — Python phải khớp tới
1e-9. Kiểm chéo SPSS/R thật chạy trong bộ giả lập trọn vòng (cần SPSS + R), không chạy ở đây (CI không có phần mềm đó).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import phan_tich_thiet_ke_dac_thu as P  # noqa: E402

GOP_DONG_NHAT = [{"s": "A", "a": 10, "n1": 100, "c": 20, "n0": 100}, {"s": "B", "a": 15, "n1": 200, "c": 30, "n0": 200},
                 {"s": "C", "a": 5, "n1": 50, "c": 8, "n0": 50}, {"s": "D", "a": 0, "n1": 40, "c": 3, "n0": 40}]
GOP_KHONG_DONG_NHAT = [{"s": "A", "a": 5, "n1": 100, "c": 20, "n0": 100},
                       {"s": "B", "a": 30, "n1": 100, "c": 25, "n0": 100},
                       {"s": "C", "a": 10, "n1": 80, "c": 30, "n0": 80}]


@pytest.mark.parametrize("hang, ky_vong", [
    # metafor 4.x: escalc(measure="RR") (add=1/2, to="only0") + rma(method="DL")
    (GOP_DONG_NHAT, (0.504921505828, 0.334811009513, 0.761461600136, 0.0, 0.0)),
    (GOP_KHONG_DONG_NHAT, (0.487955727213, 0.172718022138, 1.378552097647, 0.718000809567, 86.747682279421)),
])
def test_gop_dersimonian_laird_khop_metafor(hang, ky_vong):
    g = P.gop(hang, "s", "a", "n1", "c", "n0")
    thuc = (g["rr_gop_ngau_nhien"], g["ci_95"][0], g["ci_95"][1], g["tau2"], g["i2_pct"])
    assert all(abs(x - y) < 1e-9 for x, y in zip(thuc, ky_vong)), thuc
    assert abs(sum(t["trong_so_ngau_nhien_pct"] for t in g["tung_nghien_cuu"]) - 100) < 1e-9


def test_gop_o_khong_cong_nua_ca_bon_o_cua_nghien_cuu_do():
    yi, vi = P._o_rr(0, 40, 3, 40)
    assert math.isclose(yi, math.log((0.5 / 41) / (3.5 / 41)))
    assert math.isclose(vi, 1 / 0.5 - 1 / 41 + 1 / 3.5 - 1 / 41)
    assert P._o_rr(10, 100, 20, 100)[0] == math.log(0.5)  # không có ô 0 ⇒ không cộng


def test_auc_mann_whitney_khop_proc_ke_ca_hang_trung():
    a = P.auc_mann_whitney([0, 0, 1, 1, 0, 1, 1, 0], [1.2, 2.5, 3.1, 2.5, 0.7, 4.2, 1.9, 2.2])
    assert abs(a["auc"] - 0.84375) < 1e-12  # pROC::auc(direction = "<")
    assert P.auc_mann_whitney([0, 1, 0, 1], [1, 1, 2, 2])["auc"] == 0.5  # trùng hạng ⇒ hạng trung bình
    with pytest.raises(P.TuChoi):
        P.auc_mann_whitney([1, 1], [1, 2])


def test_chan_doan_bang_2x2_va_wilson_tai_nguong():
    # (1, 2.67) nằm ĐÚNG ngưỡng ⇒ dương tính (≥ ngưỡng, như SPSS «>= » và kịch bản R)
    hang = [{"y": y, "x": x} for y, x in ((1, 3.0), (1, 2.67), (1, 1.0), (0, 2.8), (0, 1.0), (0, 0.5), (0, 0.2))]
    kq = P.chan_doan(hang, "y", "x", 2.67)
    assert kq["bang_2x2"] == {"tp": 2, "fp": 1, "fn": 1, "tn": 3, "nguong": 2.67}
    assert kq["do_nhay"]["uoc_luong"] == 2 / 3 and kq["do_dac_hieu"]["uoc_luong"] == 0.75
    lo, hi = kq["do_nhay"]["ci_95_wilson"]
    assert 0 < lo < 2 / 3 < hi < 1


def test_du_bao_c_statistic_la_auc_cua_xac_suat_du_doan_va_brier():
    hang = [{"y": int(i % 3 == 0 or i > 25), "t": float(i), "u": float((i * 7) % 11)} for i in range(40)]
    kq = P.du_bao(hang, "y", ["t", "u"])
    assert [h["bien"] for h in kq["he_so"]] == ["(hằng số)", "t", "u"]
    assert 0.5 < kq["c_statistic"]["auc"] <= 1 and 0 < kq["brier"] < 0.25
    assert kq["n"] == 40 and kq["epv"] == round(sum(r["y"] for r in hang) / 2, 2)


def test_dinh_tinh_dem_chu_de_bo_o_trong():
    kq = P.dinh_tinh([{"c": "Sợ kim"}, {"c": "Sợ kim"}, {"c": "Chi phí"}, {"c": ""}], "c")
    assert kq["n_ban_go_bang"] == 3 and kq["chu_de"][0] == {"chu_de": "Sợ kim", "n": 2, "pct": 200 / 3}


def test_so_khop_chi_so_dai_luong_phan_mem_xuat_duoc():
    py = {"c_statistic": 0.7, "brier": 0.15, "or_tuoi": 1.02}
    assert P.so_khop(py, {"c_statistic": 0.7, "brier": 0.15})["trang_thai"] == "LECH"  # R phải đủ OR
    assert P.so_khop(py, {"c_statistic": 0.7, "brier": 0.15}, P.DAI_LUONG_SPSS["du_bao"])["trang_thai"] == "KHOP"
    assert P.so_khop(py, {"c_statistic": 0.71, "brier": 0.15, "or_tuoi": 1.02})["trang_thai"] == "LECH"


@pytest.mark.parametrize("loai, ts, lenh_r, lenh_spss", [
    ("chan_doan", {"tham_chieu": "y", "chi_so": "fib4", "nguong": 2.67}, "pROC::roc", "RANK VARIABLES=fib4"),
    ("du_bao", {"outcome": "y", "covariates": ["tuoi", "egfr"]}, "rms::validate", "LOGISTIC REGRESSION VARIABLES y"),
    ("gop", {"nhan_nghien_cuu": "s", "su_kien_can_thiep": "a", "n_can_thiep": "n1", "su_kien_chung": "c",
             "n_chung": "n0"}, 'method = "DL"', "COMPUTE tau2 = MAX(0"),
    ("dinh_tinh", {"chu_de": "chu_de"}, "table(", "AGGREGATE /OUTFILE=* /BREAK=chu_de"),
])
def test_kich_ban_r_va_spss_dung_phep_tinh(loai, ts, lenh_r, lenh_spss):
    r = P.kich_ban_r(loai, ts, Path("/tmp/dl.csv"), Path("/tmp/kq.txt"))
    sps = P.kich_ban_spss(loai, ts, Path("/tmp/dl.csv"), Path("/tmp/kq.csv"))
    assert lenh_r in r and lenh_spss in sps and "SAVE TRANSLATE" in sps


def test_chay_sap_g6_nhan_phan_tich_dac_thu_va_chan_tham_so_thua():
    import chay_sap_g6 as CS6

    assert CS6._kiem_gia_tri("loai_dac_thu", "loai", "gop") == []
    assert CS6._kiem_gia_tri("loai_dac_thu", "loai", "roc_bay") != []
    src = Path(CS6.__file__).read_text(encoding="utf-8")
    assert '"phan_tich_thiet_ke_dac_thu.py" if (pt.get("tham_so") or {}).get("loai_dac_thu")' in src
    assert "tham số không áp dụng cho phân tích" in src


def test_bien_phai_sinh_can_bac_hai_va_dich_sqrt_cua_redcap():
    import bien_phai_sinh as B
    import numpy as np
    import pandas as pd

    ct, ghi = B.dich_calc_redcap("round(([tuoi]*[ast])/([tieu_cau]*sqrt([alt])),2)")
    assert ct == "tuoi * ast / (tieu_cau * can_bac_hai(alt))" and ghi  # FIB-4 dịch được (round ⇒ ghi chú)
    cay = B.phan_tich("can_bac_hai(x)")
    kq = B.tinh_cay(cay, {"x": pd.Series([4.0, -1.0, np.nan])}, pd.RangeIndex(3))
    assert kq.iloc[0] == 2.0 and kq.iloc[1:].isna().all()  # âm/thiếu ⇒ thiếu


def test_kiem_cheo_spss_chi_so_dai_luong_xuat_duoc_r_so_du(tmp_path, monkeypatch):
    """Chạy trọn kiem_cheo với R/SPSS GIẢ: R ghi đủ đại lượng, SPSS chỉ ghi C-statistic + Brier (đúng như cú pháp SPSS
    xuất) ⇒ cả hai KHOP. Từng có lệch giả «or_…: thiếu» ở SPSS."""
    import cau_noi_r as CR
    import cau_noi_spss as S

    py = {"c_statistic": 0.7, "brier": 0.15, "or_tuoi": 1.02}
    monkeypatch.setattr(CR, "tim_r", lambda: Path("Rscript-gia"))

    def r_gia(lenh, **_kw):
        kb = Path(lenh[1]).read_text(encoding="utf-8")
        ra = kb.split('out <- file("', 1)[1].split('"', 1)[0]
        Path(ra).write_text("".join(f"{k}={v}\n" for k, v in py.items()), encoding="utf-8", newline="\n")
        return type("R", (), {"stdout": "", "stderr": ""})()

    monkeypatch.setattr(P.subprocess, "run", r_gia)
    monkeypatch.setattr(S, "_goc_tam_ngan", lambda: tmp_path)
    monkeypatch.setattr(S, "tim_spss", lambda: Path("spss-gia"))

    def spss_gia(_py, doi_so, **_kw):
        kb = Path(doi_so[1]).read_text(encoding="utf-8")
        ra = kb.split("SAVE TRANSLATE /OUTFILE='", 1)[1].split("'", 1)[0]
        Path(ra).write_text("c_statistic,brier\n0.7,0.15\n", encoding="utf-8", newline="\n")
        return 0, "", ""

    monkeypatch.setattr(S, "chay_spss", spss_gia)
    d = tmp_path / "de_tai"
    d.mkdir()
    kc = P.kiem_cheo("du_bao", {"outcome": "y", "covariates": ["tuoi"]}, [{"y": 1, "tuoi": 60}, {"y": 0, "tuoi": 50}],
                     d, "G6", py)
    assert kc["phan_mem"]["r"]["trang_thai"] == "KHOP" and kc["phan_mem"]["spss"]["trang_thai"] == "KHOP", kc
    assert (d / "r" / "G6_du_bao.R").is_file() and (d / "spss" / "G6_du_bao.sps").is_file()
    assert not (d / "scripts").exists()  # dấu vân tay xác nhận G6 tính trên scripts/ — không ghi vào đó
