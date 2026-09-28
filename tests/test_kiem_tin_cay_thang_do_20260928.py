"""Kiểm công cụ độ tin cậy thang đo cho dữ liệu pilot (28/09/2026). Dữ liệu synthetic, không PII."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))
import kiem_tin_cay_thang_do as K  # noqa: E402

# Bảng ví dụ của Shrout & Fleiss 1979 (6 đối tượng × 4 người chấm); bài báo công bố ICC(2,1) = 0,29.
SHROUT_FLEISS = np.array(
    [[9, 2, 5, 8], [6, 1, 3, 2], [8, 4, 6, 8], [7, 1, 2, 6], [10, 5, 6, 9], [6, 2, 4, 7]], dtype=float
)


def _alpha_theo_hiep_phuong_sai(x: np.ndarray) -> float:
    """Cách tính độc lập: α = k·c̄ / (v̄ + (k−1)·c̄) (v̄: phương sai TB mục, c̄: hiệp phương sai TB giữa mục)."""
    c = np.cov(x, rowvar=False, ddof=1)
    k = c.shape[0]
    v_tb = np.diag(c).mean()
    c_tb = (c.sum() - np.trace(c)) / (k * (k - 1))
    return k * c_tb / (v_tb + (k - 1) * c_tb)


def _du_lieu(seed: int = 20260928, n: int = 120, k: int = 5) -> np.ndarray:
    rng = np.random.default_rng(seed)
    nen = rng.normal(0, 1, n)
    thuc = nen[:, None] + rng.normal(0, 0.8, (n, k))
    return np.clip(np.round(3 + thuc), 1, 5)


def test_alpha_khop_cach_tinh_doc_lap():
    x = _du_lieu()
    assert K.cronbach_alpha(x) == pytest.approx(_alpha_theo_hiep_phuong_sai(x), abs=1e-12)


def test_tuong_quan_muc_tong_da_hieu_chinh_loai_chinh_muc_do():
    x = _du_lieu(n=80, k=4)
    r = K.tuong_quan_muc_tong(x)
    for j in range(4):
        con_lai = np.delete(x, j, axis=1).sum(axis=1)
        assert r[j] == pytest.approx(np.corrcoef(x[:, j], con_lai)[0, 1], abs=1e-12)
        # Không hiệu chỉnh (tính cả chính mục) luôn thổi phồng r — phải khác rõ.
        assert r[j] < np.corrcoef(x[:, j], x.sum(axis=1))[0, 1] - 1e-3


def test_ktc_feldt_bao_quanh_uoc_luong_va_hep_dan_khi_n_tang():
    a = 0.82
    d1, t1 = K.ktc_feldt(a, 40, 6)
    d2, t2 = K.ktc_feldt(a, 400, 6)
    assert d1 < a < t1 and d2 < a < t2
    assert (t2 - d2) < (t1 - d1)
    assert t1 < 1


def test_icc_2_1_khop_so_cong_bo_shrout_fleiss():
    kq = K.icc_2_1(SHROUT_FLEISS)
    assert kq["icc"] == pytest.approx(0.29, abs=0.005)
    d, t = kq["ktc95"]
    assert d < kq["icc"] < t
    # Neo hồi quy của chính công thức KTC (bài gốc chỉ công bố ước lượng điểm): 0,019–0,761.
    assert (d, t) == pytest.approx((0.019, 0.761), abs=0.005)


def test_icc_hai_lan_do_giong_het_bang_1():
    y = np.column_stack([np.arange(10.0), np.arange(10.0)])
    assert K.icc_2_1(y)["icc"] == pytest.approx(1.0)


def test_xep_loai_koo_li():
    assert [K.xep_loai_koo_li(v) for v in (0.4, 0.6, 0.8, 0.95)] == ["kém", "vừa", "tốt", "rất tốt"]


def test_phan_tich_thang_ma_thieu_va_san_tran():
    df = pd.DataFrame({"A": [1, 1, 5, 9, 2], "B": [1, 1, 5, 3, 2], "C": [1, 1, 5, 4, 3]})
    sub = K.chuan_hoa_muc(df, ["A", "B", "C"], [9.0])
    kq = K.phan_tich_thang("T", sub, 1, 5)
    assert kq["n_dung"] == 4 and kq["n_loai_vi_thieu"] == 1
    assert kq["ty_le_thieu_theo_muc"]["A"] == pytest.approx(0.2)
    assert kq["san_tran"]["ty_le_san"] == pytest.approx(0.5)
    assert kq["san_tran"]["ty_le_tran"] == pytest.approx(0.25)
    assert any("sàn" in c for c in kq["canh_bao"])


def test_khong_khai_thang_thi_khong_doan_san_tran():
    x = _du_lieu(n=30, k=3)
    sub = pd.DataFrame(x, columns=["A", "B", "C"])
    assert K.phan_tich_thang("T", sub, None, None)["san_tran"] is None


def test_gia_tri_ngoai_thang_bi_chan():
    sub = pd.DataFrame({"A": [1, 2, 7], "B": [1, 2, 3]})
    with pytest.raises(K.LoiDauVao, match="ngoài"):
        K.phan_tich_thang("T", sub, 1, 5)


def test_muc_xep_tang_dan_theo_r_muc_tong():
    rng = np.random.default_rng(1)
    x = _du_lieu(n=200, k=4)
    nhieu = rng.integers(1, 6, 200).astype(float)
    sub = pd.DataFrame(np.column_stack([x, nhieu]), columns=["A", "B", "C", "D", "NHIEU"])
    kq = K.phan_tich_thang("T", sub, 1, 5)
    assert kq["muc"][0]["muc"] == "NHIEU"
    r = [m["r_muc_tong_hieu_chinh"] for m in kq["muc"]]
    assert r == sorted(r)


def test_cli_lap_lai_khong_in_ma_dinh_danh(tmp_path, capsys):
    x = _du_lieu(n=40, k=3)
    ma = [f"BN-BIMAT-{i:03d}" for i in range(40)]
    lan1 = pd.DataFrame(x, columns=["A", "B", "C"]).assign(ma=ma)
    lan2 = lan1.copy()
    lan2.loc[::5, "A"] = np.clip(lan2.loc[::5, "A"] + 1, 1, 5)
    p1, p2 = tmp_path / "l1.csv", tmp_path / "l2.csv"
    lan1.to_csv(p1, index=False)
    lan2.sample(frac=1, random_state=3).to_csv(p2, index=False)  # đảo thứ tự: phải ghép theo mã
    rc = K.main([str(p1), "--muc", "A", "B", "C", "--min", "1", "--max", "5",
                 "--lap-lai", str(p2), "--khoa-id", "ma", "--json"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "BN-BIMAT" not in out
    kq = json.loads(out)
    assert kq["lap_lai"]["n_ghep_cap"] == 40
    assert kq["lap_lai"]["icc"] > 0.9


def test_cli_loi_dau_vao_tra_ma_2(tmp_path, capsys):
    p = tmp_path / "d.csv"
    pd.DataFrame({"A": [1, 2], "B": ["x", "y"]}).to_csv(p, index=False)
    assert K.main([str(p), "--muc", "A", "B"]) == 2
    assert K.main([str(p), "--muc", "A", "KHONG_CO"]) == 2
    assert K.main([str(p), "--muc", "A", "B", "--min", "1"]) == 2
    assert "LỖI ĐẦU VÀO" in capsys.readouterr().err
