"""Hồi quy đa biến với hiệp biến DẠNG CHỮ có ô rỗng (việc treo từ 14/11/2026, sửa 17/11/2026).

Trước bản vá: `multivariate_model(df, "kq", "nhom", ["tuoi", "nghe"], "binary")` với `nghe` là chuỗi (cong_chuc /
nong_dan / khac, ô rỗng) trả {"error": "Pandas data cast to numpy dtype of object…", "note": "… không hội tụ"} —
pandas 3 trả biến giả kiểu bool, trộn với cột số thành mảng object. Đây là lỗi thật (hàm vốn mã hoá chữ bằng
get_dummies), không phải giới hạn có chủ ý. Phép thử đối chiếu với công thức C(nghe) của statsmodels (mã hoá độc lập).
"""
from __future__ import annotations

import csv
import math
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import run_stats_analysis as R  # noqa: E402

pytest.importorskip("statsmodels")
import statsmodels.formula.api as smf  # noqa: E402


@pytest.fixture
def df(tmp_path):
    rng = random.Random(20261117)
    p = tmp_path / "d.csv"
    with p.open("w", encoding="utf-8", newline="") as fh:  # da-nen: bo-qua (CSV RFC 4180, dữ liệu thử)
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["nhom", "tuoi", "nghe", "kq"])
        for _ in range(400):
            n = rng.random() < 0.5
            nghe = "" if rng.random() < 0.15 else rng.choice(["cong_chuc", "nong_dan", "khac"])
            w.writerow([int(n), rng.randint(30, 80), nghe, int(rng.random() < 0.3 + 0.2 * n)])
    return R.load_data(str(p))


def test_logistic_ma_hoa_hiep_bien_chu_va_o_rong_la_thieu(df):
    r = R.multivariate_model(df, "kq", "nhom", ["tuoi", "nghe"], "binary")
    assert "error" not in r, r
    du = df.dropna(subset=["nghe"])
    assert r["model"] == "logistic" and r["n"] == len(du)
    ten = {x["variable"]: x for x in r["results"]}
    assert set(ten) == {"nhom", "tuoi", "nghe_khac", "nghe_nong_dan"}  # tham chiếu = mức đầu (cong_chuc)
    doc_lap = smf.logit("kq ~ nhom + tuoi + C(nghe)", data=du).fit(disp=False)
    for bien, khoa in (("nghe_khac", "C(nghe)[T.khac]"), ("nghe_nong_dan", "C(nghe)[T.nong_dan]"), ("nhom", "nhom")):
        assert math.isclose(ten[bien]["OR_adj"], round(math.exp(doc_lap.params[khoa]), 3), abs_tol=1e-3), bien


def test_tuyen_tinh_ma_hoa_hiep_bien_chu(df):
    r = R.multivariate_model(df, "tuoi", "nhom", ["nghe"], "continuous")
    assert r["model"] == "linear" and {x["variable"] for x in r["results"]} == {"nhom", "nghe_khac", "nghe_nong_dan"}


def test_loi_that_su_khong_bi_goi_la_khong_hoi_tu(df, monkeypatch):
    """Lỗi bất kỳ trong khối fit (vd ma trận suy biến) ⇒ ghi chú nói đúng bản chất, không khẳng định «không hội tụ»."""
    def hong(*_a, **_k):
        raise ValueError("ma trận suy biến")

    monkeypatch.setattr(R.sm, "Logit", hong)
    r = R.multivariate_model(df, "kq", "nhom", ["tuoi"], "binary")
    assert r["error"] == "ma trận suy biến" and "không chạy được" in r["note"]
