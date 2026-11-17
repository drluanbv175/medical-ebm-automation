"""Bảng 1 + nguồn gốc khoá cho tóm tắt G6 của phân tích ĐẶC THÙ, và khối ước lượng đặc thù ở G7 (17/11/2026).

Giả lập trọn vòng 17/11 đo được: tóm tắt G6 của định tính · dự báo · tổng quan–gộp · chẩn đoán
(phan_tich_thiet_ke_dac_thu) (1) không có `table1`, (2) không có `data_lock.sha256`/`generated` ⇒ G7
(doc_tom_tat_g6_hop_le) fail-closed và bản thảo là khung trống — nhãn «(GIẢ LẬP — hồ sơ chưa có)» của bộ giả lập từng
che thành «đạt»; (3) G7 không đọc `dac_thu`.
Các phép thử khoá cả ba chỗ.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import phan_tich_thiet_ke_dac_thu as P  # noqa: E402
import run_g7_auto as G7  # noqa: E402
import run_stats_analysis as RSA  # noqa: E402


def _df_du_bao():
    return pd.DataFrame({
        "record_id": [f"R{i:03d}" for i in range(40)],
        "tuoi": [50 + i for i in range(40)], "gioi": [i % 2 for i in range(40)],
        "nyha": [1 + i % 4 for i in range(40)], "ngay_kham": ["2027-03-01"] * 40,
        "ghi_chu": [f"ghi chú tự do số {i}" for i in range(40)],
        "nhap_vien_12t": [1 if i % 4 == 0 else 0 for i in range(40)]})


def _tu_dien(d: Path) -> None:
    import csv

    d.mkdir(parents=True, exist_ok=True)
    with (d / "_bo-bien-rieng.csv").open("w", encoding="utf-8", newline="") as fh:  # da-nen: bo-qua (RFC 4180)
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["Variable / Field Name", "Field Type", "Choices, Calculations, OR Slider Labels"])
        w.writerow(["nyha", "radio", "1, I | 2, II | 3, III | 4, IV"])
        w.writerow(["gioi", "radio", "0, Nữ | 1, Nam"])  # 2 lựa chọn ⇒ giữ số (nhị phân)


@pytest.fixture
def gia_khoa(tmp_path, monkeypatch):
    def _dung(df):
        monkeypatch.setattr(P, "_doc_df_khoa", lambda study, can, loc=None: (df.copy(), tmp_path / "x.csv", {}))
        monkeypatch.setattr(P, "thu_muc_de_tai", lambda study: tmp_path / "dt")
        _tu_dien(tmp_path / "dt")
    return _dung


def test_du_bao_bang1_theo_ket_cuc_co_kiem_dinh_va_nhan_lua_chon(gia_khoa):
    gia_khoa(_df_du_bao())
    t1 = P.bang1_dac_thu("X", "du_bao", {"outcome": "nhap_vien_12t", "covariates": ["tuoi"]})
    assert t1["groups"] == ["0", "1"] and t1["n_per_group"] == {0: 30, 1: 10}
    bien = [r["variable"] for r in t1["rows"]]
    assert bien == ["tuoi", "gioi", "nyha"]  # bỏ định danh, ngày, văn bản tự do, chính biến chia nhóm
    nyha = next(r for r in t1["rows"] if r["variable"] == "nyha")
    assert nyha["type"] == "categorical" and "III:" in nyha["grp_0"]  # mã → nhãn từ từ điển, không «2.00 [1.00–3.00]»
    assert all("p" in r for r in t1["rows"])


def test_dinh_tinh_mot_nhom_khong_kiem_dinh_va_bo_ket_cuc_chu_de(gia_khoa):
    df = pd.DataFrame({"ma_nguoi_tham_gia": [f"P{i}" for i in range(12)], "tuoi": list(range(40, 52)),
                       "gioi": [i % 2 for i in range(12)], "chu_de": ["A", "B", "C"] * 4})
    gia_khoa(df)
    t1 = P.bang1_dac_thu("X", "dinh_tinh", {"chu_de": "chu_de"})
    assert t1["groups"] == [RSA.NHOM_TOAN_BO] and [r["variable"] for r in t1["rows"]] == ["tuoi", "gioi"]
    assert not any(r.get("p") is not None or r.get("test") for r in t1["rows"])


def test_gop_dac_diem_nghien_cuu_bo_nhan_nghien_cuu(gia_khoa):
    df = pd.DataFrame({"study_id": [f"TN{i}" for i in range(6)], "n_can_thiep": [100, 200, 300, 400, 500, 600],
                       "theo_doi_thang": [12, 18, 24, 30, 36, 42]})
    gia_khoa(df)
    t1 = P.bang1_dac_thu("X", "gop", {"nhan_nghien_cuu": "study_id"})
    assert [r["variable"] for r in t1["rows"]] == ["n_can_thiep", "theo_doi_thang"] and t1["n_per_group"] == {
        RSA.NHOM_TOAN_BO: 6}


def test_kinh_te_khong_co_bang1_rieng():
    assert P.bang1_dac_thu("X", "kinh_te", {}) is None


def test_chay_ghi_nguon_goc_khoa_va_table1(tmp_path, monkeypatch):
    import cau_noi_spss as S

    d = tmp_path / "dt"
    _tu_dien(d)
    monkeypatch.setattr(P, "_g4_da_khoa", lambda study: None)
    monkeypatch.setattr(P, "thu_muc_de_tai", lambda study: d)
    monkeypatch.setattr(P, "doc_du_lieu", lambda study, can, loc=None: (
        [{"chu_de": "A"}, {"chu_de": "B"}, {"chu_de": "A"}], tmp_path / "khoa.csv", 0))
    monkeypatch.setattr(P, "_doc_df_khoa", lambda study, can, loc=None: (
        pd.DataFrame({"tuoi": [40, 50, 60], "chu_de": ["A", "B", "A"]}), tmp_path / "khoa.csv", {}))
    monkeypatch.setattr(S, "tim_du_lieu_khoa", lambda study: (tmp_path / "khoa.csv", {"sha256": "ab" * 32}))
    assert P.chay("X", "G6", "dinh_tinh", {"chu_de": "chu_de"}, False) == 0
    tom = json.loads((d / "G6_analysis_summary.json").read_text(encoding="utf-8"))
    assert tom["data_lock"]["sha256"] == "ab" * 32 and tom["generated"]
    assert tom["table1"]["rows"][0]["variable"] == "tuoi" and (d / "G6_table1_descriptive.txt").is_file()


# ─────────────────────────────────────────────────────────────────────────────────────── G7 khối ước lượng đặc thù
_KQ = {
    "dinh_tinh": {"n_ban_go_bang": 20, "so_chu_de": 2, "chu_de": [
        {"chu_de": "Gia đình hỗ trợ", "n": 8, "pct": 40.0, "ty_le": 0.4, "ci_95_wilson": [0.2188, 0.6134]},
        {"chu_de": "Ngại hạ đường huyết", "n": 6, "pct": 30.0, "ty_le": 0.3, "ci_95_wilson": [0.1455, 0.519]}]},
    "du_bao": {"he_so": [{"bien": "(hằng số)", "or": 0.0137, "ci_95": [0.004, 0.046], "p": 3.7e-12},
                         {"bien": "tuoi", "or": 1.039, "ci_95": [1.025, 1.053], "p": 2.8e-08}],
               "c_statistic": {"auc": 0.7059, "ci_95": [0.6604, 0.7513]}, "brier": 0.1474, "n": 900,
               "n_bien_co": 182, "epv": 45.5},
    "gop": {"rr_gop_ngau_nhien": 0.6932, "ci_95": [0.6404, 0.7505], "rr_gop_co_dinh": 0.6932,
            "ci_95_co_dinh": [0.6404, 0.7505], "tau2": 0.0, "q": 2.8532, "df": 14, "i2_pct": 0.0, "k": 15,
            "tung_nghien_cuu": [{"nghien_cuu": "TN01-2016", "rr": 0.6899, "ci_95": [0.5177, 0.9194]}]},
    "chan_doan": {"auc": {"auc": 0.5997, "ci_95": [0.4318, 0.7675]},
                  "do_nhay": {"uoc_luong": 0.3529, "ci_95_wilson": [0.1731, 0.587], "k": 6, "n": 17},
                  "do_dac_hieu": {"uoc_luong": 0.8056, "ci_95_wilson": [0.6497, 0.9025], "k": 29, "n": 36},
                  "ppv": {"uoc_luong": 0.4615, "ci_95_wilson": [0.2321, 0.7086], "k": 6, "n": 13},
                  "npv": {"uoc_luong": 0.725, "ci_95_wilson": [0.5717, 0.8389], "k": 29, "n": 40},
                  "lr_duong": 1.8151, "lr_am": 0.8032},
}


@pytest.mark.parametrize("loai, phai_co", [
    ("dinh_tinh", ["| Gia đình hỗ trợ | 8 | 0.4 | 0.2188–0.6134 |", "20 bản gỡ băng"]),
    ("du_bao", ["C-statistic (AUC trong mẫu) = 0.7059", "| `tuoi` | 1.039 |"]),
    ("gop", ["RR gộp (hiệu ứng ngẫu nhiên) = 0.6932", "I² = 0.0%", "| TN01-2016 | 0.6899 |"]),
    ("chan_doan", ["AUC = 0.5997", "| Độ nhạy | 0.3529 |", "LR+ = 1.8151"]),
])
def test_g7_khoi_dac_thu_chep_nguyen_van_va_qua_tu_kiem(loai, phai_co):
    tt = {"loai_dac_thu": loai, "dac_thu": _KQ[loai], "n_total": 20}
    dong = G7._khoi_uoc_luong_g6(tt, "G6_analysis_summary.json")
    van = "\n".join(dong)
    for x in phai_co:
        assert x in van, (loai, x)
    assert "(hằng số)" not in van and "chỉ ghi N phân tích" not in van
    assert G7.kiem_so_trich_g6(van, json.dumps(tt, ensure_ascii=False)) == []  # mọi số có nguyên văn trong G6


def test_g7_khong_doc_dac_thu_la_khung_trong():
    """Đối chứng: tóm tắt KHÔNG có dac_thu/ước lượng chuẩn ⇒ vẫn là ô [CẦN KẾT QUẢ THẬT], không bịa."""
    dong = G7._khoi_uoc_luong_g6({"n_total": 20}, "G6_analysis_summary.json")
    assert any("chỉ ghi N phân tích" in x for x in dong)


def test_bang1_tho_chuyen_duoc_sang_khuon_tom_tat_ma_g7_chep():
    t1 = RSA.table1_descriptive(pd.DataFrame({"g": ["Toàn bộ"] * 4, "tuoi": [40, 50, 60, 70]}), "g", ["tuoi"])
    tom = RSA.bang1_cho_tom_tat(t1)
    assert G7._bang1_tu_g6(tom, {"Toàn bộ": 4})  # G7 đọc được (n_per_group + rows)


def test_g7_co_mau_ke_hoach_lay_n_chot_g3_khi_khong_tinh_theo_luc():
    """Định tính/tổng quan–gộp: n_adjusted = 0 (không tính theo lực) ⇒ bản thảo từng in «… (G3): N = 0»."""
    kw = dict(study="S", topic="T", n_sr=1, n_rct=1, n_guideline=1, research_gaps=["k"], pmids=["11111111"],
              pmid_meta={}, design_code="qualitative", design_primary="Định tính", reporting_std="SRQR",
              irb_number="[CẦN]", icf_version="[CẦN]", registration="[CẦN]", n_total=0, n_adjusted=0, alpha=0.05,
              power=0.8, effect_val=None, effect_type=None, formula_used="", g4_status="PENDING", g4_lock_date=None,
              target_journal="[CẦN]", word_limit=3500, run_date="2026-11-17", g3_n_chot=20)
    m = G7.generate_manuscript(**kw)
    assert "Phân tích cuối: N = 20 (kế hoạch)" in m and "N = 0 (kế hoạch)" not in m
    kw.update(n_adjusted=218, g3_n_chot=None)
    assert "Phân tích cuối: N = 218 (kế hoạch)" in G7.generate_manuscript(**kw)


def test_run_stats_thiet_ke_mo_ta_co_bang1_mot_nhom_va_loc_bien():
    df = pd.DataFrame({"record_id": [f"R{i}" for i in range(30)], "ngay_kham": ["2027-03-01"] * 30,
                       "tuoi": list(range(40, 70)), "gioi": [i % 2 for i in range(30)],
                       "thuoc_khac": [f"thuốc ghi tay {i}" for i in range(30)],
                       "kiem_soat": [i % 3 == 0 for i in range(30)]})
    bien = RSA.bien_bang1_mo_ta(df, list(df.columns), ("kiem_soat",))
    assert bien == ["tuoi", "gioi"]  # bỏ định danh, ngày, văn bản tự do, kết cục
    t1 = RSA.table1_descriptive(df.assign(_n=RSA.NHOM_TOAN_BO), "_n", bien)
    tom = RSA.bang1_cho_tom_tat(t1)
    assert tom["groups"] == [RSA.NHOM_TOAN_BO] and tom["n_per_group"] == {RSA.NHOM_TOAN_BO: 30}
    assert G7._bang1_tu_g6(tom, {RSA.NHOM_TOAN_BO: 30})
