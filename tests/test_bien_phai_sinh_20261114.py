"""F1 (14/11/2026) — biến phái sinh tự động: tools/bien_phai_sinh.py + nối vào run_stats_analysis/cầu nối SPSS·R.

Soát chuỗi SPSS/R theo yêu cầu bác sĩ: `_bien-phai-sinh.csv` (C1a 12 biến, BTM 23 biến gồm kết cục chính `xn_du`) không
công cụ nào đọc ⇒ phân tích không chạy được. Bộ test này giữ: ngôn ngữ công thức chỉ nhận tập con an toàn; ngữ nghĩa
thiếu (logic ba trị) đúng; dấu công thức gắn lần duyệt; phân tích chính DỪNG khi công thức chưa duyệt; cầu nối SPSS/R
tự tính lại độc lập; Python = R (= SPSS khi máy có) từng ô. Dữ liệu giả, không PII.
"""

from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import json
import math
import shutil
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
import bien_phai_sinh as B  # noqa: E402

pd = pytest.importorskip("pandas")
np = pytest.importorskip("numpy")

COT_TD = ["Variable / Field Name", "Form Name", "Field Type", "Field Label", "Choices, Calculations, OR Slider Labels",
          "Text Validation Type OR Show Slider Number", "Identifier?", "Field Annotation"]  # fmt: skip
COT_PS = ["ten_bien", "nhan", "kieu", "dinh_nghia", "bien_nguon", "quy_tac_ma_thieu", "dung_o", "nguon", "cong_thuc",
          "lap_k", "nhan_gia_tri", "nguoi_duyet"]  # fmt: skip


def _td(d: Path, hang: list[tuple[str, str, str, str]], ten: str = "_bo-bien-rieng.csv") -> None:
    with open(d / ten, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(COT_TD)
        for t, loai, lc, kt in hang:
            w.writerow([t, "f", loai, t, lc, kt, "", ""])


def _ps(d: Path, dong: list[tuple], duyet: bool = True) -> None:
    with open(d / "_bien-phai-sinh.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(COT_PS)
        for x in dong:
            ten, ct = x[0], x[1]
            lk = x[2] if len(x) > 2 else ""
            ngt = x[3] if len(x) > 3 else ""
            nd = f"THONG_KE_VIEN:TEST:2026-11-14:{B.dau_cong_thuc(ten, ct, lk)}" if duyet else ""
            w.writerow([ten, f"nhãn {ten}", "", "", "", "", "", "", ct, lk, ngt, nd])


def _kq(d: Path, study: str = "T"):
    bien = B.doc_dac_ta(d)
    dm = B.doc_danh_muc_tu_dien(d, study)
    return B.kiem_dac_ta(bien, dm), dm


def _tinh(ct: str, du_lieu: dict, td: list | None = None, tmp: Path | None = None, ten: str = "kq_ps"):
    """Tính MỘT công thức trên khung dữ liệu nhỏ (giá trị dạng chữ như CSV)."""
    tmp.mkdir(exist_ok=True)
    _td(tmp, td or [(c, "text", "", "") for c in du_lieu])
    _ps(tmp, [(ten, ct)])
    kq, dm = _kq(tmp)
    assert not kq.loi, kq.loi
    df = pd.DataFrame({k: [None if v is None else str(v) for v in vs] for k, vs in du_lieu.items()}, dtype=object)
    return B.tinh_df(df, kq, dm, [ten])[ten].tolist()


def _bang(x: list) -> list:
    return [None if (isinstance(v, float) and math.isnan(v)) else v for v in x]


# ───────────────────────── ngôn ngữ công thức ─────────────────────────


@pytest.mark.parametrize(
    "ct, mau",
    [
        ("__import__('os').system('x')", "không được phép"),
        ("eval('1')", "không có trong danh sách"),
        ("__import__('os')", "không có trong danh sách"),
        ("a.b", "không được phép"),
        ("a[0]", "không được phép"),
        ("1 < a < 3", "một phép"),
        ("a + 'x'", "không dùng được"),
        ("creat_{k}_gt", "lap_k"),
        ('ho("a_{k}", 1, 2)', "chỉ dùng làm danh sách cột"),
        ("nhom(a, [60, 40], [1, 2, 3])", "tăng dần"),
        ("nhom(a, [40, 60], [1, 2])", "cần 3 mã"),
        ('co_it_nhat([a], "=>", 3)', "phép so sánh"),
        ('ngay("2026-02-30")', "không phải ngày"),
        ("dem([a, 1], [9])", "TÊN cột"),
        ("lambda: 1", "không được phép"),
        ("tb_hop_le([a], hop_le=[5, 1])", "hop_le"),
        ("tb_hop_le([a], ty_le_toi_thieu=1.5)", "ty_le_toi_thieu"),
        ("neu(a, 1)", "3 tham số"),
        ("bo_ma(a, [])", "rỗng"),
        ("trong(a, [1], x=1)", "không có tham số tên"),
    ],
)
def test_cong_thuc_ngoai_tap_con_bi_tu_choi(ct, mau):
    with pytest.raises(B.LoiCongThuc, match=mau):
        B.phan_tich(ct)


def test_cong_thuc_hop_le_va_cot_tham_chieu():
    cay = B.phan_tich('neu(g1 >= 4 and not la_thieu(x), dem(ho("q_{k}", 1, 3), [9]), -2.5) ** 2')
    assert B.cot_cua_cay(cay) == ["g1", "x", "q_1", "q_2", "q_3"]
    assert B.phan_tich('ngay("1970-01-11")') == {"t": "so", "v": 10.0}


# ───────────────────────── ngữ nghĩa (Python) ─────────────────────────


def test_tb_hop_le_ty_le_va_ma_khong_ap_dung(tmp_path):
    du = {"a": [1, 1, 7, None, 1, 6], "b": [2, 2, 7, None, 8, 2], "c": [7, 3, 7, None, 3, 3],
          "d": [9, 3, 7, None, 3, 3]}  # fmt: skip
    r = _tinh("tb_hop_le([a, b, c, d], hop_le=[1, 5], khong_ap_dung=[7], ty_le_toi_thieu=0.8)", du, tmp=tmp_path / "t")
    # ca1: áp dụng 3 (1,2,9) hợp lệ 2 ⇒ 2/3 < 0,8 ⇒ thiếu · ca2: 4/4 ⇒ 2,25 · ca3: toàn mã 7 ⇒ thiếu
    # ca4: trống ⇒ áp dụng 4 hợp lệ 0 ⇒ thiếu · ca5: 8 ngoài miền ⇒ 3/4 < 0,8 · ca6: 6 ngoài miền ⇒ 3/4 < 0,8
    assert _bang(r) == [None, 2.25, None, None, None, None]
    r0 = _tinh("tb_hop_le([a, b, c, d], hop_le=[1, 5], khong_ap_dung=[7])", du, tmp=tmp_path / "t0")
    # ca5 (1, 8, 3, 3): 8 ngoài miền ⇒ hợp lệ 1, 3, 3 ⇒ 7/3 · ca6 (6, 2, 3, 3): hợp lệ 2, 3, 3 ⇒ 8/3
    assert _bang(r0) == [1.5, 2.25, None, None, pytest.approx(7 / 3), pytest.approx(8 / 3)]


def test_logic_ba_tri_kleene_va_so_sanh_thieu(tmp_path):
    du = {"p": [1, 1, 0, 0, None, None, None], "q": [1, None, 0, None, 1, 0, None]}
    assert _bang(_tinh("p == 1 and q == 1", du, tmp=tmp_path / "a")) == [1.0, None, 0.0, 0.0, None, 0.0, None]
    assert _bang(_tinh("p == 1 or q == 1", du, tmp=tmp_path / "b")) == [1.0, 1.0, 0.0, None, 1.0, None, None]
    assert _bang(_tinh("not (p == 1)", du, tmp=tmp_path / "c")) == [0.0, 0.0, 1.0, 1.0, None, None, None]
    assert _bang(_tinh("neu(p, 5, 6)", du, tmp=tmp_path / "d")) == [5.0, 5.0, 6.0, 6.0, None, None, None]
    g = {"g1": [5, 3, 9, 6, None]}
    assert _bang(_tinh("neu(trong(g1, [1, 2, 3, 4, 5]), g1 >= 4, thieu())", g, tmp=tmp_path / "e")) == [
        1.0, 0.0, None, None, None]  # fmt: skip


def test_bo_ma_trong_nhom_bien_va_la_thieu(tmp_path):
    du = {"x": [39.999, 40, 59.5, 60, None, "KDD", 998]}
    assert _bang(_tinh("nhom(x, [40, 60], [1, 2, 3])", du, tmp=tmp_path / "n")) == [1, 2, 2, 3, None, None, 3]
    assert _bang(_tinh("bo_ma(x, [998])", du, tmp=tmp_path / "b")) == [39.999, 40, 59.5, 60, None, None, None]
    assert _bang(_tinh("la_thieu(x)", du, tmp=tmp_path / "l")) == [0, 0, 0, 0, 1, 1, 0]
    assert _bang(_tinh("trong(x, [40, 60])", du, tmp=tmp_path / "t")) == [0, 1, 0, 1, None, None, 0]


def test_dem_tat_ca_co_gt_co_it_nhat(tmp_path):
    du = {"a": [9, None, 1, 9], "b": [9, None, 2, 1], "c": [9, 9, None, 3]}
    assert _bang(_tinh("dem([a, b, c], [9])", du, tmp=tmp_path / "d")) == [3, 1, 0, 1]
    assert _bang(_tinh("dem([a, b, c], [9], ke_ca_trong=True)", du, tmp=tmp_path / "e")) == [3, 3, 1, 1]
    assert _bang(_tinh("tat_ca([a, b, c], [9], ke_ca_trong=True)", du, tmp=tmp_path / "f")) == [1, 1, 0, 0]
    assert _bang(_tinh("dem_co_gt([a, b, c])", du, tmp=tmp_path / "g")) == [3, 1, 2, 3]
    # mã 9 là SỐ (không phải ô thiếu) ⇒ 9 ≥ 3 tính là thoả — công thức muốn loại mã phải bo_ma tường minh
    assert _bang(_tinh('co_it_nhat([a, b, c], ">=", 3)', du, tmp=tmp_path / "h")) == [1, 1, 0, 1]


def test_ngay_moi_nhat_va_hai_lan_cach_90_ngay(tmp_path):
    td = [("g_1", "text", "", "number"), ("g_2", "text", "", "number"), ("n_1", "text", "", "date_dmy"),
          ("n_2", "text", "", "date_dmy")]  # fmt: skip
    du = {"g_1": [50, 50, 50, 70, 50], "g_2": [55, 55, 80, 50, None],
          "n_1": ["2026-01-01", "2026-01-01", "2026-05-01", "2026-03-01", "2026-03-01"],
          "n_2": ["2026-03-31", "2026-04-01", "2026-05-01", "2026-01-01", "2026-09-01"]}  # fmt: skip
    hai = 'co_hai_lan(ho("g_{k}", 1, 2), ho("n_{k}", 1, 2), "<", 60, cach_ngay=90)'
    # 2026-01-01 → 03-31 = 89 ngày (không đủ) · → 04-01 = 90 ngày (đủ)
    assert _bang(_tinh(hai, du, td, tmp_path / "h")) == [0, 1, 0, 0, 0]
    moi = 'gt_moi_nhat(ho("g_{k}", 1, 2), ho("n_{k}", 1, 2))'
    assert _bang(_tinh(moi, du, td, tmp_path / "m")) == [55, 55, 80, 70, 50]  # ca3 trùng ngày ⇒ k lớn hơn


def _ckd_doc_lap(scr: float, tuoi: float, nu: bool) -> float:
    """Inker 2021 (PMID 34554658) viết lại độc lập:
    142 × min(Scr/κ,1)^α × max(Scr/κ,1)^−1,200 × 0,9938^tuổi × 1,012 (nữ)."""
    kap, alp = (0.7, -0.241) if nu else (0.9, -0.302)
    return 142 * min(scr / kap, 1) ** alp * max(scr / kap, 1) ** -1.2 * 0.9938**tuoi * (1.012 if nu else 1.0)


def test_ckd_epi_2021_khop_cong_thuc_doc_lap(tmp_path):
    du = {"s": [0.6, 0.7, 1.0, 2.4, 1.0, None, 0], "t": [50, 50, 60, 72, 60, 50, 50], "g": [2, 2, 1, 2, None, 1, 1]}
    r = _tinh("ckd_epi_2021(s, t, g == 2)", du, tmp=tmp_path / "c")
    ky = [_ckd_doc_lap(0.6, 50, True), _ckd_doc_lap(0.7, 50, True), _ckd_doc_lap(1.0, 60, False),
          _ckd_doc_lap(2.4, 72, True)]  # fmt: skip
    assert r[:4] == pytest.approx(ky, rel=1e-12)
    assert _bang(r[4:]) == [None, None, None]  # giới thiếu · Scr thiếu · Scr 0 (vô hạn) ⇒ thiếu


def test_ngay_chu_va_chia_cho_khong_la_thieu(tmp_path):
    td = [("d", "text", "", "date_dmy"), ("x", "text", "", "integer")]
    du = {"d": ["2026-07-01", "2026-06-30", "KDD", "01/07/2026", None], "x": [0, 2, 4, None, 1]}
    assert _bang(_tinh('d < ngay("2026-07-01")', du, td, tmp_path / "a")) == [0, 1, None, None, None]
    assert _bang(_tinh("10 / x", du, td, tmp_path / "b")) == [None, 5.0, 2.5, None, 10.0]
    assert _bang(_tinh("(0 - x) ** 0.5", du, td, tmp_path / "c")) == [0.0, None, None, None, None]


# ───────────────────────── đặc tả, dấu duyệt, phụ thuộc ─────────────────────────


def test_lap_k_khai_trien_va_dau_mot_cho_ca_ho(tmp_path):
    _td(tmp_path, [(f"c_{k}", "text", "", "number") for k in (1, 2, 3)])
    _ps(tmp_path, [("e_k", "c_{k} * 2", "1-3"), ("tong", 'dem_co_gt(ho("e_{k}", 1, 3))')])
    kq, _dm = _kq(tmp_path)
    assert [b.ten for b in kq.bien] == ["e_1", "e_2", "e_3", "tong"]
    assert kq.bien[1].cong_thuc == "c_2 * 2" and len({b.dau for b in kq.bien[:3]}) == 1
    assert kq.thu_tu.index("tong") > max(kq.thu_tu.index(f"e_{k}") for k in (1, 2, 3))
    assert set(kq.trang_thai.values()) == {"DA_DUYET"}


def test_dau_cong_thuc_gan_lan_duyet(tmp_path):
    dau = B.dau_cong_thuc("x", "a + 1", "")
    assert B.trang_thai_duyet("", dau) == "CHUA_DUYET"
    assert B.trang_thai_duyet(f"PI:BB-1:2026-11-20:{dau}", dau) == "DA_DUYET"
    assert B.trang_thai_duyet(f"PI:BB-1:2026-11-20:{dau}", B.dau_cong_thuc("x", "a + 2", "")) == "HET_HIEU_LUC"
    assert B.trang_thai_duyet("PI:[CẦN DUYỆT]:2026-11-20:" + dau, dau) == "SAI_DANG"
    assert B.trang_thai_duyet(f"PI:2026-11-20:{dau}", dau) == "SAI_DANG"
    assert dau == B.dau_cong_thuc("x", "  a   +  1 ", "")  # khoảng trắng không đổi dấu


def test_kiem_dac_ta_bat_cot_vang_calc_vong_va_trung_ten(tmp_path):
    _td(tmp_path, [("a", "text", "", ""), ("bmi", "calc", "[w]/[h]", "")])
    _ps(tmp_path, [("x1", "khong_co + 1"), ("x2", "bmi * 2"), ("v1", "v2 + 1"), ("v2", "v1 + 1"), ("a", "1"),
                   ("x3", "x1 + 1"), ("ok", "a + 1"), ("ngoai", "@g6_trong_so_survey"), ("trong", "")])  # fmt: skip
    kq, _dm = _kq(tmp_path)
    assert "khong_co" in kq.loi["x1"]
    assert "trường calc" in kq.loi["x2"]
    assert "vòng phụ thuộc" in kq.loi["v1"] and "vòng phụ thuộc" in kq.loi["v2"]
    assert "trùng một cột dữ liệu" in kq.loi["a"]
    assert "phụ thuộc biến chưa tính được" in kq.loi["x3"]
    assert kq.trang_thai["ok"] == "DA_DUYET" and kq.thu_tu == ["ok"]
    assert kq.trang_thai["ngoai"] == "NGOAI_TANG" and kq.trang_thai["trong"] == "CHUA_CO_CONG_THUC"


def test_nhan_gia_tri_sai_dang_bi_bat(tmp_path):
    _td(tmp_path, [("a", "text", "", "")])
    _ps(tmp_path, [("x", "a", "", "1 G1 | 2, G2")])
    with pytest.raises(B.LoiCongThuc, match="mã, nhãn"):
        B.doc_dac_ta(tmp_path)


def test_checkbox_thanh_cot_ba_gach(tmp_path):
    _td(tmp_path, [("thuoc", "checkbox", "1, A | 2, B | 4, D", "")])
    dm = B.doc_danh_muc_tu_dien(tmp_path, "T")
    assert {"thuoc___1", "thuoc___2", "thuoc___4"} <= dm.cot and "thuoc" not in dm.cot


# ───────────────────────── dùng trong phân tích chính ─────────────────────────


def _de_tai_pt(tmp_path: Path, duyet: bool, gia_lap: bool = False) -> tuple[Path, object]:
    d = tmp_path / "exports" / "PT"
    d.mkdir(parents=True)
    _td(d, [("g1", "radio", "1, a | 2, b | 3, c | 4, d | 5, e | 9, k", ""), ("q", "text", "", "integer")],
        ten="G5_REDCap_dictionary_PT.csv")  # fmt: skip
    _ps(d, [("hl", "neu(trong(g1, [1, 2, 3, 4, 5]), g1 >= 4, bo_ma(g1, [9]))"), ("q2", "q * 2"), ("thua", "q + 100")],
        duyet=duyet)  # fmt: skip
    if gia_lap:
        (d / "study_meta.json").write_text(json.dumps({"study_kind": "synthetic_test"}), encoding="utf-8", newline="\n")
    df = pd.DataFrame({"g1": [5, 2, 9, 4], "q": [1, 2, 3, None]})
    return d, df


def test_phan_tich_chinh_tinh_bien_can_va_ghi_dau(tmp_path):
    d, df = _de_tai_pt(tmp_path, duyet=True)
    df2, info = B.ap_dung_cho_phan_tich(df, d, "PT", ["hl", "nhom_khac", None, "q2"])
    assert _bang(df2["hl"].tolist()) == [1.0, 0.0, None, 1.0] and "thua" not in df2  # chỉ biến CẦN
    assert set(info["bien"]) == {"hl", "q2"} and info["bien"]["hl"]["dau"] == B.dau_cong_thuc(
        "hl", "neu(trong(g1, [1, 2, 3, 4, 5]), g1 >= 4, bo_ma(g1, [9]))", "")
    assert info["sha256_tep"] == hashlib.sha256((d / "_bien-phai-sinh.csv").read_bytes()).hexdigest()
    assert "g1" in df2 and list(df.columns) == ["g1", "q"]  # dữ liệu khoá không bị sửa


def test_phan_tich_chinh_dung_khi_cong_thuc_chua_duyet(tmp_path):
    d, df = _de_tai_pt(tmp_path, duyet=False)
    with pytest.raises(B.TuChoi, match="chưa được THỐNG KÊ VIÊN/PI duyệt"):
        B.ap_dung_cho_phan_tich(df, d, "PT", ["hl"])
    df2, info = B.ap_dung_cho_phan_tich(df, d, "PT", ["g1"])  # không dùng biến phái sinh ⇒ không chặn
    assert info is None and df2 is df


def test_de_tai_gia_lap_chi_canh_bao(tmp_path):
    d, df = _de_tai_pt(tmp_path, duyet=False, gia_lap=True)
    df2, info = B.ap_dung_cho_phan_tich(df, d, "PT", ["hl"])
    assert "hl" in df2 and info["canh_bao"] and "CHƯA DUYỆT" in info["canh_bao"][0]


def test_cau_noi_tu_choi_khi_cong_thuc_doi_sau_luot_python(tmp_path):
    d, df = _de_tai_pt(tmp_path, duyet=True)
    _df2, info = B.ap_dung_cho_phan_tich(df, d, "PT", ["hl"])
    k = tmp_path / "k.csv"
    df.to_csv(k, index=False)
    ma, ds, muc = B.khoi_cho_cau_noi(d, {"bien_phai_sinh": info}, "r", k)
    assert ds == ["hl"] and muc["hl"] == ["0", "1"] and '[["hl"]] <-' in ma
    _ps(d, [("hl", "neu(trong(g1, [1, 2, 3, 4, 5]), g1 >= 3, bo_ma(g1, [9]))")])
    with pytest.raises(B.TuChoi, match="ĐỔI sau lượt phân tích Python"):
        B.khoi_cho_cau_noi(d, {"bien_phai_sinh": info}, "spss", k)
    assert B.khoi_cho_cau_noi(d, {}, "r", k) == ("", [], {})


def test_ma_chu_bat_dau_trung_cau_noi_spss():
    import cau_noi_spss as S

    assert B.MA_CHU_BAT_DAU == S.MA_CHU_BAT_DAU


def test_spss_cu_phap_dung_value_va_number_f40_0(tmp_path):
    _td(tmp_path, [("a", "text", "", "integer"), ("d", "text", "", "date_dmy"), ("s", "text", "", "")])
    _ps(tmp_path, [("x", 'a + s + (d - ngay("2026-01-01"))')])
    kq, dm = _kq(tmp_path)
    ma, _ = B.cu_phap_spss(kq, None, ten_spss={"a": ("A_SPSS", True), "s": ("s", False)}, ngay=dm.ngay)
    assert "VALUE(A_SPSS)" in ma and f"<= {B.MA_CHU_BAT_DAU}" in ma
    assert "NUMBER(LTRIM(RTRIM(s)), F40.0)" in ma and "F40.10" not in ma  # F40.10 hiểu «5» thành 5e-10
    assert "NUMBER(d, SDATE10)" in ma and "DELETE VARIABLES ebm_bps_" in ma


# ───────────────────────── dòng lệnh ─────────────────────────


def test_cli_tinh_tu_choi_thu_muc_ra_trong_repo_va_kiem(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(B, "BASE", tmp_path)
    d = tmp_path / "exports" / "CL"
    d.mkdir(parents=True)
    _td(d, [("a", "text", "", "integer")])
    _ps(d, [("x", "a + 1"), ("hong", "khong_co + 1")])
    data = tmp_path / "ngoai.csv"
    data.write_text("a\n1\n2\n", encoding="utf-8", newline="\n")
    assert B.main(["tinh", "--study", "CL", "--data", str(data), "--ra", str(tmp_path / "ra"), "--chi", "x"]) == 3
    ra = tmp_path.parent / f"{tmp_path.name}_ra"
    try:
        assert B.main(["tinh", "--study", "CL", "--data", str(data), "--ra", str(ra), "--chi", "x"]) == 0
        assert pd.read_csv(ra / "ngoai_phai_sinh.csv")["x"].tolist() == [2, 3]
    finally:
        shutil.rmtree(ra, ignore_errors=True)
    capsys.readouterr()
    assert B.main(["kiem", "--study", "CL", "--json"]) == 1  # còn công thức lỗi
    j = json.loads(capsys.readouterr().out)
    assert j["dem"] == {"DA_DUYET": 1, "LOI": 1}
    assert B.main(["kiem", "--study", "KHONG-CO"]) == 3
    assert B.main(["doi-chieu", "--study", "CL", "--data", str(data), "--chi", "x", "--khong-r", "--khong-spss"]) == 0


# ───────────────────────── đối chiếu thật với R / SPSS ─────────────────────────


def _du_lieu_doi_chieu(d: Path) -> Path:
    _td(d, [("a1", "text", "", "integer"), ("a2", "text", "", "integer"), ("a3", "text", "", "integer"),
            ("g", "text", "", "integer"), ("s_1", "text", "", "number"), ("s_2", "text", "", "number"),
            ("n_1", "text", "", "date_dmy"), ("n_2", "text", "", "date_dmy"), ("tuoi", "text", "", "integer")],
        ten="G5_REDCap_dictionary_DC.csv")  # fmt: skip
    _ps(d, [("tb", "tb_hop_le([a1, a2, a3], hop_le=[1, 5], khong_ap_dung=[7], ty_le_toi_thieu=0.6)"),
            ("e_k", "ckd_epi_2021(s_{k}, tuoi, g == 2)", "1-2"),
            ("cuoi", 'gt_moi_nhat(ho("e_{k}", 1, 2), ho("n_{k}", 1, 2))'),
            ("hai", 'co_hai_lan(ho("e_{k}", 1, 2), ho("n_{k}", 1, 2), "<", 60, cach_ngay=90)'),
            ("nh", "nhom(cuoi, [30, 60, 90], [4, 3, 2, 1])"),
            ("lg", "(dem([a1, a2, a3], [9], ke_ca_trong=True) >= 2 or la_thieu(tuoi)) and not trong(g, [1])"),
            ("th", 'neu(la_thieu(n_1), thieu(), (ngay("2026-12-31") - n_1) / 30.44)')])  # fmt: skip
    (d / "_ma-thieu-theo-bien.csv").write_text("bien,ma,nhan,pham_vi,nguon\n*,KDD,Không đọc được,dự án,thử\n",
                                               encoding="utf-8", newline="\n")  # fmt: skip
    rng = np.random.default_rng(14112026)
    n = 160
    hang = {
        "a1": rng.choice(["1", "2", "3", "4", "5", "7", "9", "", "KDD"], n),
        "a2": rng.choice(["1", "2", "3", "4", "5", "7", "9", ""], n),
        "a3": rng.choice(["1", "2", "3", "4", "5", "7", ""], n),
        "g": rng.choice(["1", "2", ""], n),
        "s_1": [f"{x:.2f}" if rng.random() < 0.8 else "" for x in rng.uniform(0.4, 4, n)],
        "s_2": [f"{x:.2f}" if rng.random() < 0.7 else "" for x in rng.uniform(0.4, 4, n)],
        "n_1": [f"2026-{rng.integers(1, 13):02d}-{rng.integers(1, 29):02d}" if rng.random() < 0.85 else "KDD"
                for _ in range(n)],  # fmt: skip
        "n_2": [f"2026-{rng.integers(1, 13):02d}-{rng.integers(1, 29):02d}" if rng.random() < 0.85 else ""
                for _ in range(n)],  # fmt: skip
        "tuoi": [str(x) if rng.random() < 0.85 else "" for x in rng.integers(20, 90, n)],
    }
    p = d / "du_lieu.csv"
    pd.DataFrame(hang).to_csv(p, index=False)
    return p


def test_python_khop_r_tung_o(tmp_path):
    try:
        B._tim_rscript()
    except B.KhongDoDuoc:
        pytest.skip("máy không có Rscript")
    d = tmp_path / "DC"
    d.mkdir()
    p = _du_lieu_doi_chieu(d)
    kq, dm = _kq(d, "DC")
    assert not kq.loi
    py = B.tinh_df(B._doc_csv_chu(p), kq, dm, None)
    rk = B.chay_r(kq, list(py.columns), p, dm, tmp_path)
    lech = {c: B.so_tung_o(py[c], rk[c], "r")["so_lech"] for c in py.columns}
    assert lech == dict.fromkeys(py.columns, 0), lech


def test_python_khop_spss_tung_o(tmp_path):
    import cau_noi_spss as S

    try:
        S.tim_spss()
    except Exception:  # noqa: BLE001
        pytest.skip("máy không có IBM SPSS Statistics")
    d = tmp_path / "DC"
    d.mkdir()
    p = _du_lieu_doi_chieu(d)
    kq, dm = _kq(d, "DC")
    py = B.tinh_df(B._doc_csv_chu(p), kq, dm, None)
    sk = B._spss_vung_ngan(kq, list(py.columns), p, d, "DC")
    lech = {c: B.so_tung_o(py[c], sk[c], "spss")["so_lech"] for c in py.columns}
    assert lech == dict.fromkeys(py.columns, 0), lech


# ───────────────────────── nối vào run_stats_analysis + cầu nối ─────────────────────────


def _main_run_stats(tmp_path: Path, monkeypatch, duyet: bool) -> tuple[dict | None, Path, str]:
    pytest.importorskip("statsmodels")
    import run_stats_analysis as RSA

    locked = {"g2_status": "LOCKED", "g4_status": "LOCKED", "g5_status": "LOCKED"}
    monkeypatch.setattr(RSA, "BASE", tmp_path)
    monkeypatch.setattr(RSA, "_load_checkpoint", lambda study, gate: dict(locked))
    monkeypatch.setattr(RSA, "_ledger_approved", lambda *a, **k: True)
    monkeypatch.setattr(RSA.GC, "g2_quality_contract_satisfied", lambda *a, **k: True)
    monkeypatch.setattr(RSA.GC, "resolve_design_code", lambda *a, **k: ("cross_sectional", None))
    monkeypatch.setattr(RSA.G5Q, "evaluate_study", lambda *a, **k: {"status": RSA.G5Q.STATUS_LOCKED})
    d = tmp_path / "exports" / "RS"
    (d / "05_clean_locked").mkdir(parents=True)
    rng = np.random.default_rng(7)
    n = 160
    nhom = rng.integers(0, 2, n)
    p_hl = 1 / (1 + np.exp(-(-0.2 + 0.9 * nhom)))
    g1 = np.where(rng.random(n) < p_hl, rng.choice([4, 5], n), rng.choice([1, 2, 3], n))
    k = d / "05_clean_locked" / "k.csv"
    pd.DataFrame({"nhom": nhom, "tuoi": rng.integers(20, 80, n), "g1": g1}).to_csv(k, index=False)
    _td(d, [("nhom", "radio", "0, A | 1, B", ""), ("tuoi", "text", "", "integer"),
            ("g1", "radio", "1, a | 2, b | 3, c | 4, d | 5, e", "")], ten="G5_REDCap_dictionary_RS.csv")  # fmt: skip
    _ps(d, [("hl", "neu(trong(g1, [1, 2, 3, 4, 5]), g1 >= 4, 0)")], duyet=duyet)
    man = {"locked_dataset_path": "05_clean_locked/k.csv", "sha256": hashlib.sha256(k.read_bytes()).hexdigest(),
           "status": "LOCKED_FOR_ANALYSIS", "analysis_allowed": True}  # fmt: skip
    monkeypatch.setattr(RSA, "_require_locked_analysis_dataset", lambda study, _d: man)
    monkeypatch.setattr(sys, "argv", ["run_stats_analysis.py", "--data", str(k), "--study", "RS", "--gate", "G6",
                                      "--outcome", "hl", "--group", "nhom", "--covariates", "tuoi",
                                      "--outcome-type", "binary", "--n-imputations", "2"])  # fmt: skip
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        tom = RSA.main()
    return tom, d, buf.getvalue()


def test_run_stats_ket_cuc_phai_sinh_da_duyet_chay_va_ghi_tom_tat(tmp_path, monkeypatch):
    tom, d, ra = _main_run_stats(tmp_path, monkeypatch, duyet=True)
    luu = json.loads((d / "G6_analysis_summary.json").read_text(encoding="utf-8"))
    assert luu["bien_phai_sinh"]["bien"]["hl"]["duyet"] == "DA_DUYET"
    assert luu["primary_outcome"] and "Biến phái sinh tính từ" in ra


def test_run_stats_ket_cuc_phai_sinh_chua_duyet_dung(tmp_path, monkeypatch):
    with pytest.raises(SystemExit) as e:
        _main_run_stats(tmp_path, monkeypatch, duyet=False)
    assert e.value.code == 1
    assert not (tmp_path / "exports" / "RS" / "G6_analysis_summary.json").exists()


def test_cau_noi_r_cu_phap_chen_khoi_phai_sinh(tmp_path, monkeypatch):
    import cau_noi_r as R
    import cau_noi_spss as S

    _main_run_stats(tmp_path, monkeypatch, duyet=True)
    monkeypatch.setattr(S, "EXPORTS", tmp_path / "exports")
    d = tmp_path / "exports" / "RS"
    (d / "DATA_LOCK_manifest.json").write_text(json.dumps({
        "locked_dataset_path": "05_clean_locked/k.csv",
        "sha256": hashlib.sha256((d / "05_clean_locked" / "k.csv").read_bytes()).hexdigest(),
        "lock_date": "2026-11-14", "status": "LOCKED_FOR_ANALYSIS", "analysis_allowed": True}), encoding="utf-8",
        newline="\n")  # fmt: skip
    with contextlib.redirect_stdout(io.StringIO()):
        assert R.main(["cu-phap", "--study", "RS"]) == R.MA_OK
    vb = (d / "r" / "RS_phan_tich.R").read_text(encoding="utf-8")
    vt_nap, vt_ps = vb.index("D <- doc_nhu_pandas(DU_LIEU)"), vb.index('D[["hl"]] <- as.numeric(')
    assert vt_nap < vt_ps < vb.index("KET <- list()")  # tính SAU khi nạp, TRƯỚC phân tích
    assert json.loads((d / "r" / "dac_ta.json").read_text(encoding="utf-8"))["bien_phai_sinh"] == ["hl"]


def test_cau_noi_spss_them_bien_va_chen_sau_get_file(tmp_path, monkeypatch):
    import cau_noi_spss as S

    _main_run_stats(tmp_path, monkeypatch, duyet=True)
    monkeypatch.setattr(S, "EXPORTS", tmp_path / "exports")
    d = tmp_path / "exports" / "RS"
    man = {"sav": str(d / "spss" / "RS_khoa.sav"), "nguon_csv": str(d / "05_clean_locked" / "k.csv"),
           "bien": [{"cot": c, "ten": c, "so": True, "bo": False, "muc": m, "nhan": c, "nhan_gia_tri": {},
                     "ma_chu": {}, "ma_thieu_so": []}
                    for c, m in (("nhom", ["0", "1"]), ("tuoi", None), ("g1", ["1", "2", "3", "4", "5"]))]}  # fmt: skip
    man2 = S.them_bien_phai_sinh("RS", man, "G6")
    them = [b for b in man2["bien"] if b.get("phai_sinh")]
    assert [(b["ten"], b["muc"]) for b in them] == [("hl", ["0", "1"])] and len(man["bien"]) == 3
    dt = {"outcome": "hl", "group": "nhom", "covariates": ["tuoi"], "outcome_type": "binary", "time": None,
          "event": None, "cot_cum": None, "don_vi_phoi_nhiem": None}  # fmt: skip
    vb, _cb, _phu = S.cu_phap_phan_tich("RS", man2, dt, tmp_path / "kq")
    assert vb.index("GET FILE=") < vb.index("COMPUTE hl = ") < vb.index("OMS /SELECT ALL")
    assert S.them_bien_phai_sinh("KHAC", man, "G6") is man  # không có tóm tắt ⇒ giữ nguyên


def test_run_g6_auto_chi_nhan_bien_phai_sinh_tinh_duoc(tmp_path):
    import run_g6_auto as G6A

    _td(tmp_path, [("a", "text", "", "integer")], ten="G5_REDCap_dictionary_G6T.csv")
    _ps(tmp_path, [("xn_du", "a >= 1"), ("hong", "khong_co + 1"), ("chua", "")], duyet=False)
    da_biet, loi = G6A.bien_phai_sinh_da_biet(tmp_path, "G6T")
    assert da_biet == {"xn_du": "CHUA_DUYET"} and loi is None
    (tmp_path / "_bien-phai-sinh.csv").write_text("ten_bien,nhan_gia_tri\nx,sai dạng\n", encoding="utf-8", newline="\n")
    da_biet, loi = G6A.bien_phai_sinh_da_biet(tmp_path, "G6T")
    assert da_biet == {} and "mã, nhãn" in loi
