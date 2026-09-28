"""N10 (28/09/2026) — kiểm định Brant cho giả định tỷ lệ odds trong hồi quy logistic thứ tự của engine G6.

Trước bản vá, Bảng 4 thứ tự chỉ in OR theo từng ngưỡng để người đọc tự so. Kiểm: (1) dữ liệu đúng giả định ⇒
tỷ lệ p < 0,05 quanh 5%; (2) vi phạm ở MỘT biến ⇒ kiểm định tổng và đúng biến đó có p nhỏ, biến kia không;
(3) có cụm ⇒ cảnh báo giả định độc lập; (4) tách hoàn toàn ⇒ báo lỗi, không bịa χ²; (5) Bảng 4 in kết quả.
Dữ liệu synthetic, không PII.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))
import run_stats_analysis as RSA  # noqa: E402

pytest.importorskip("statsmodels.api")
pytest.importorskip("scipy")


def _du_lieu(seed: int, n: int = 800, vi_pham: bool = False) -> pd.DataFrame:
    """Kết cục 1–4 sinh từ logistic tích luỹ; vi phạm = hệ số của `nhom` tăng dần theo ngưỡng."""
    rng = np.random.default_rng(seed)
    x = rng.normal(size=n)
    z = rng.integers(0, 2, n)
    cuts = np.array([-1.0, 0.0, 1.0])
    bz = np.array([0.0, 0.8, 1.6]) if vi_pham else np.array([0.8, 0.8, 0.8])
    eta = 0.7 * x[:, None] + bz[None, :] * z[:, None] - cuts[None, :]
    y = (rng.random(n)[:, None] < 1 / (1 + np.exp(-eta))).sum(1) + 1
    return pd.DataFrame({"hl": y, "nhom": z, "tuoi": x, "ban": rng.integers(0, 20, n)})


def _brant(df, cum=None):
    return RSA.ordinal_model(df, "hl", "nhom", ["tuoi"], cluster_col=cum)["brant"]


def test_ty_le_sai_duong_tinh_gan_5_phan_tram():
    lan = 120
    sai = sum(_brant(_du_lieu(s))["tong"]["p"] < 0.05 for s in range(lan))
    assert sai / lan <= 0.12


def test_vi_pham_mot_bien_bi_chi_ra_dung_bien():
    br = _brant(_du_lieu(1, vi_pham=True))
    assert br["tong"]["p"] < 0.001 and br["tong"]["df"] == 4
    assert br["theo_bien"]["nhom"]["p"] < 0.001 and br["theo_bien"]["nhom"]["df"] == 2
    assert br["theo_bien"]["tuoi"]["p"] > 0.01
    assert "canh_bao" not in br


def test_co_cum_canh_bao_gia_dinh_doc_lap():
    br = _brant(_du_lieu(2), cum="ban")
    assert "giả định quan sát độc lập" in br["canh_bao"][0]


def test_tach_hoan_toan_bao_loi_khong_bia_so():
    df = _du_lieu(3)
    df.loc[df["nhom"] == 1, "hl"] = 4  # nhom=1 luôn ở mức cao nhất ⇒ tách hoàn toàn
    br = _brant(df)
    assert "tong" not in br and "không hội tụ/tách hoàn toàn" in br["loi"]


def test_bang4_in_brant():
    od = RSA.ordinal_model(_du_lieu(1, vi_pham=True), "hl", "nhom", ["tuoi"])
    txt = RSA.format_ordinal_text(od)
    assert "KIỂM ĐỊNH BRANT" in txt and "Tổng thể: χ² =" in txt and "[CẦN THỐNG KÊ VIÊN]" in txt


def _brant_tham_chieu(df):
    """Cài đặt độc lập (viết lại trong test) — ma trận hiệp phương sai đầy đủ, đối xứng — để đối chiếu χ²."""
    import statsmodels.api as sm
    from scipy import stats

    X = sm.add_constant(df[["nhom", "tuoi"]].astype(float)).to_numpy()
    y = df["hl"].to_numpy()
    muc = sorted(np.unique(y))[:-1]
    b, pi, inv = [], [], []
    for k in muc:
        f = sm.Logit((y > k).astype(float), X).fit(disp=False)
        pr = f.predict(X)
        b.append(f.params)
        pi.append(pr)
        inv.append(np.linalg.inv(X.T @ (X * (pr * (1 - pr))[:, None])))
    m, q = len(muc), X.shape[1]
    blocks = [[None] * m for _ in range(m)]
    for i in range(m):
        for j in range(m):
            lo, hi = min(i, j), max(i, j)
            c = inv[lo] @ (X.T @ (X * (pi[hi] * (1 - pi[lo]))[:, None])) @ inv[hi]
            blocks[i][j] = c if i <= j else c.T
    V = np.block(blocks)
    bb = np.concatenate(b)
    D = []
    for t in range(1, m):
        for v in (1, 2):
            r = np.zeros(m * q)
            r[v], r[t * q + v] = 1, -1
            D.append(r)
    D = np.array(D)
    d = D @ bb
    chi = float(d @ np.linalg.solve(D @ V @ D.T, d))
    return chi, stats.chi2.sf(chi, len(D))


@pytest.mark.parametrize("seed, vi_pham", [(5, False), (1, True), (9, False)])
def test_khop_cai_dat_tham_chieu_doc_lap(seed, vi_pham):
    df = _du_lieu(seed, vi_pham=vi_pham)
    chi, p = _brant_tham_chieu(df)
    t = _brant(df)["tong"]
    assert t["chi2"] == pytest.approx(chi, abs=1e-3)
    assert t["p"] == pytest.approx(p, abs=1e-4)


def test_tach_gan_hoan_toan_bao_loi():
    df = _du_lieu(4)
    df.loc[(df["nhom"] == 1) & (df["hl"] == 1), "hl"] = 2  # nhom=1 không bao giờ ở mức 1 ⇒ tách tại Y > 1
    br = _brant(df)
    assert "tong" not in br and "không hội tụ/tách hoàn toàn" in br["loi"]



class _LogitGia:
    """Logit giả: fit trả hệ số hợp lệ nhưng báo không hội tụ, hoặc phát cảnh báo tách hoàn toàn."""

    def __init__(self, y, X, kieu):
        self._X, self._kieu = X, kieu

    def fit(self, **_):
        import warnings

        from statsmodels.tools.sm_exceptions import PerfectSeparationWarning

        if self._kieu == "canh_bao":
            warnings.warn("tách hoàn toàn (giả lập)", PerfectSeparationWarning, stacklevel=1)
        X, kieu = self._X, self._kieu

        class _KQ:
            params = np.zeros(X.shape[1])
            mle_retvals = {"converged": kieu != "khong_hoi_tu"}

            @staticmethod
            def predict(_x):
                return np.full(len(X), 0.5)

        return _KQ()


@pytest.mark.parametrize("kieu", ["khong_hoi_tu", "canh_bao"])
def test_moi_chot_hoi_tu_chan_doc_lap(monkeypatch, kieu):
    monkeypatch.setattr(RSA.sm, "Logit", lambda y, X: _LogitGia(y, X, kieu))
    br = RSA.kiem_dinh_brant(pd.Series([1, 2, 3, 1, 2, 3]), pd.DataFrame({"a": [0.1, 0.5, 0.2, 0.9, 0.3, 0.7]}),
                             [1, 2, 3])
    assert "tong" not in br and "không hội tụ/tách hoàn toàn" in br["loi"]
