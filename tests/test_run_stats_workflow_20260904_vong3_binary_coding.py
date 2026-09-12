"""Hồi quy phát hiện #1 của Workflow đối kháng đa-agent vòng 3 (2026-09-04, CRITICAL) trong
tools/run_stats_analysis.py::compare_primary_outcome() — nhánh "binary".

detect_var_type() chỉ đòi ĐÚNG 2 giá trị khác nhau để gán "binary", KHÔNG đòi hai giá trị đó
là {0,1}. compare_primary_outcome() (trước bản vá) tính số biến cố bằng `int(s.sum())` —
CHỈ đúng khi mã hoá literal là 0=không biến cố/1=biến cố. Với mọi kiểu mã hoá 2 mức khác
(REDCap 1/2, 0/2, chuỗi "0"/"1" object dtype) con số này SAI mà KHÔNG báo lỗi/cảnh báo gì:

  · mã 0/2 (đúng ca trong finding): 100 bệnh nhân/nhóm, biến cố thật 10%/30% (mã "2"=biến
    cố) → OR/RD SAI trước khi vá (or_crude=6.0, risk_diff=0.40) so với đúng (~3.86, 0.20).
  · mã 1/2, 20/20 mỗi nhóm: .sum() cộng dồn CẢ mã "1" (không biến cố) ⇒ events có thể VƯỢT
    QUÁ n (vd 25/20 = 125%), và khi đó `n0-e0` âm khiến sqrt() ra NaN trong CI — rò rỉ NaN
    vào báo cáo mà không cảnh báo.
  · mã chuỗi "0"/"1" (dtype object/str): Series.sum() trên object dtype = NỐI CHUỖI, không
    phải cộng số — int() trên chuỗi số nối vẫn thành công ⇒ số biến cố phi lý (vd
    events=1010000000) mà không lỗi/cảnh báo nào.

table1_descriptive() (dòng ~365) đã có đúng cách làm từ trước — đếm số lần xuất hiện của
giá trị LỚN NHẤT trong 2 giá trị khác nhau của TOÀN BỘ cột — bản vá áp lại đúng quy ước đó
cho compare_primary_outcome() để nhất quán trong cùng file.

Nguyên tắc viết test: gọi THẲNG compare_primary_outcome() với DataFrame dựng tay có đáp án
đã biết trước (tỷ lệ biến cố thật tính tay), không grep chuỗi trong mã nguồn.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(REPO_ROOT))
import run_stats_analysis as RSA  # noqa: E402


class TestMaHoa02DungTiLeThat:
    """★★ Ca chính, đúng nguyên văn kịch bản trong finding: mã 0=không biến cố /
    2=biến cố, 100 bệnh nhân/nhóm, tỷ lệ biến cố THẬT 10%/30%."""

    def _du_lieu(self):
        # Nhóm 0: 10/100 biến cố (mã 2), còn lại mã 0. Nhóm 1: 30/100 biến cố.
        outcome_0 = [2] * 10 + [0] * 90
        outcome_1 = [2] * 30 + [0] * 70
        return pd.DataFrame({
            "group": [0] * 100 + [1] * 100,
            "outcome": outcome_0 + outcome_1,
        })

    def test_dem_dung_bien_co_khong_dem_ca_ma_khong_bien_co(self):
        df = self._du_lieu()
        res = RSA.compare_primary_outcome(df, "outcome", "group", outcome_type="binary")
        assert "error" not in res, res
        assert res["group_0"]["events"] == 10
        assert res["group_0"]["n"] == 100
        assert res["group_0"]["pct"] == pytest.approx(10.0)
        assert res["group_1"]["events"] == 30
        assert res["group_1"]["pct"] == pytest.approx(30.0)

    def test_or_va_rd_khop_dap_an_tinh_tay(self):
        df = self._du_lieu()
        res = RSA.compare_primary_outcome(df, "outcome", "group", outcome_type="binary")
        # OR thô đúng = (30/70)/(10/90) = 0.42857/0.11111 ≈ 3.857
        assert res["or_crude"] == pytest.approx(3.857, abs=0.01)
        # Risk difference đúng = 0.30 - 0.10 = 0.20
        assert res["risk_diff"] == pytest.approx(0.20, abs=1e-6)
        # KHÔNG được ra giá trị SAI mà bản lỗi cũ từng tính (OR=6.0, RD=0.40)
        assert res["or_crude"] != pytest.approx(6.0, abs=0.05)
        assert res["risk_diff"] != pytest.approx(0.40, abs=1e-6)


class TestMaHoa12KhongVuotQuaN:
    """Mã 1=không biến cố / 2=biến cố, hai nhóm cân bằng 20/20 — trước bản vá,
    .sum() cộng dồn CẢ mã 'không biến cố' khiến events có thể VƯỢT n (vd 125%)."""

    def test_events_khong_bao_gio_vuot_qua_n(self):
        rng_outcome_0 = [1] * 15 + [2] * 5     # 5/20 biến cố (mã 2)
        rng_outcome_1 = [1] * 10 + [2] * 10    # 10/20 biến cố (mã 2)
        df = pd.DataFrame({
            "group": [0] * 20 + [1] * 20,
            "outcome": rng_outcome_0 + rng_outcome_1,
        })
        res = RSA.compare_primary_outcome(df, "outcome", "group", outcome_type="binary")
        assert "error" not in res, res
        assert res["group_0"]["events"] == 5
        assert res["group_0"]["n"] == 20
        assert 0 <= res["group_0"]["pct"] <= 100
        assert res["group_1"]["events"] == 10
        assert 0 <= res["group_1"]["pct"] <= 100

    def test_khong_ro_ri_nan_vao_ci(self):
        """Với dữ liệu hợp lệ (không có nhóm 0%/100% biến cố), CI RD/OR phải là số
        hữu hạn thật, không phải NaN — trước bản vá, events>n có thể khiến sqrt()
        nhận số âm và rò rỉ NaN vào risk_diff_ci_95."""
        import math
        df = pd.DataFrame({
            "group": [0] * 20 + [1] * 20,
            "outcome": ([1] * 15 + [2] * 5) + ([1] * 10 + [2] * 10),
        })
        res = RSA.compare_primary_outcome(df, "outcome", "group", outcome_type="binary")
        lo, hi = res["risk_diff_ci_95"]
        assert math.isfinite(lo) and math.isfinite(hi), res


class TestMaHoaChuoiKhongNoiChuoi:
    """Mã chuỗi '0'/'1' (dtype object) — Series.sum() trên object dtype là NỐI
    CHUỖI, không phải cộng số; trước bản vá int() trên chuỗi số nối vẫn thành
    công nên ra số biến cố phi lý (vd events > 1 tỷ) mà không lỗi/cảnh báo."""

    def test_khong_noi_chuoi_thanh_so_phi_ly(self):
        df = pd.DataFrame({
            "group": [0] * 10 + [1] * 10,
            "outcome": pd.array((["1"] * 3 + ["0"] * 7) + (["1"] * 6 + ["0"] * 4),
                                 dtype="object"),
        })
        res = RSA.compare_primary_outcome(df, "outcome", "group", outcome_type="binary")
        assert "error" not in res, res
        assert res["group_0"]["events"] == 3
        assert res["group_0"]["n"] == 10
        assert res["group_0"]["events"] <= res["group_0"]["n"]
        assert res["group_1"]["events"] == 6
        assert res["group_1"]["events"] <= res["group_1"]["n"]


class TestMaHoa01GocKhongDoiHanhVi:
    """Đối chứng bắt buộc: mã 0/1 gốc (trường hợp phổ biến nhất, đã đúng từ trước)
    KHÔNG được đổi hành vi sau bản vá."""

    def test_ma_01_goc_van_dung_nhu_cu(self):
        df = pd.DataFrame({
            "group": [0] * 50 + [1] * 50,
            "outcome": ([1] * 10 + [0] * 40) + ([1] * 25 + [0] * 25),
        })
        res = RSA.compare_primary_outcome(df, "outcome", "group", outcome_type="binary")
        assert "error" not in res, res
        assert res["group_0"]["events"] == 10
        assert res["group_0"]["pct"] == pytest.approx(20.0)
        assert res["group_1"]["events"] == 25
        assert res["group_1"]["pct"] == pytest.approx(50.0)


class TestQuaHaiGiaTriBiChanCung:
    """Bảo vệ đường gọi TƯỜNG MINH outcome_type='binary' (bỏ qua auto-detect):
    cột thật sự có >2 giá trị khác nhau phải bị CHẶN với thông điệp rõ, không
    được âm thầm tính effect trên giả định sai."""

    def test_ba_gia_tri_khac_nhau_bi_chan_voi_thong_diep_ro(self):
        df = pd.DataFrame({
            "group": [0] * 9 + [1] * 9,
            "outcome": ([0, 1, 2] * 3) + ([0, 1, 2] * 3),
        })
        res = RSA.compare_primary_outcome(df, "outcome", "group", outcome_type="binary")
        assert "error" in res
        assert "2 giá trị" in res["error"] or "3 giá trị" in res["error"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
