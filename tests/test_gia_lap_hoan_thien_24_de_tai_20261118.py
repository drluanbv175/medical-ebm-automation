"""Hồi quy 18/11/2026 — đo 24 đề tài giả lập (16 khung + 8 chân thực) qua hội đồng trách nhiệm cổng tìm ra 5 chỗ
agent «còn việc» mà KHÔNG phải do đề tài thiếu, mà do bộ giả lập hoặc bộ chấm lệch luật:

E. G3-T2 báo «biến định danh — G5-AUTO-02 sẽ chặn» cho trường PHÂN LOẠI có mã («tc_dien_thoai» Có/Không) trong khi
   G5-AUTO-02 bỏ qua trường phân loại từ 17/11 ⇒ hội đồng dùng đúng luật của G5.
C. G6-AUTO-02/03 của đề tài ĐỊNH TÍNH khai seed/alpha «không áp dụng» treo «cần xem» vĩnh viễn ⇒ ĐẠT khi đo được:
   thiết kế đã chốt là định tính VÀ script không có bước ngẫu nhiên / kiểm định thống kê nào.
B. 6 kịch bản thêm ghi min/max rỗng cho mọi trường số ⇒ G3-T3 «trường số thiếu khoảng hợp lệ».
G9-T1. Bộ giả lập ghi «G9_REPORTING_CHECKLIST_…» trong khi hội đồng đòi «REPORTING_CHECKLIST_<mã>.md».
D. Tổng quan gộp: bộ giả lập không ghi `06_phan_tich_R/study_level_extraction.csv` (G5-T2).
"""
from __future__ import annotations

import csv
import json
import sys
import types
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS))

import g6_quality_gate as G6Q  # noqa: E402
import gia_lap_kich_ban_them as KBT  # noqa: E402
import gia_lap_tron_vong as TV  # noqa: E402
import hoi_dong_cong as HD  # noqa: E402


# ── E. G3-T2 dùng đúng luật biến định danh của G5-AUTO-02 ─────────────────────────────────────────────────────────
def _dong(ten: str, loai: str) -> list:
    return [ten, "phieu", "", loai, f"Nhãn {ten}", "", "", "", "", "", "y"]


@pytest.mark.parametrize("loai", ["yesno", "truefalse", "radio", "dropdown", "checkbox"])
def test_g3t2_truong_phan_loai_ten_giong_dinh_danh_khong_bi_bao(monkeypatch, tmp_path, loai):
    monkeypatch.setattr(HD, "_nap_bo_bien", lambda _o, _s: ([_dong("record_id", "text"),
                                                           _dong("tc_dien_thoai", loai)], []))
    loi = HD._kiem_bo_bien_so(tmp_path, "S")
    assert not any("biến định danh" in x for x in loi), loi


@pytest.mark.parametrize("loai", ["text", "notes"])
def test_g3t2_truong_tu_do_ten_dinh_danh_van_bi_bao(monkeypatch, tmp_path, loai):
    monkeypatch.setattr(HD, "_nap_bo_bien", lambda _o, _s: ([_dong("record_id", "text"),
                                                           _dong("so_dien_thoai", loai)], []))
    loi = HD._kiem_bo_bien_so(tmp_path, "S")
    assert any("biến định danh" in x and "so_dien_thoai" in x for x in loi), loi


# ── C. G6 đề tài định tính: «không áp dụng» đo được thì ĐẠT ────────────────────────────────────────────────────
_SAP = ("# SAP\n\n### §10 Tái lập\n\nSeed: không áp dụng — phân tích chủ đề không có bước ngẫu nhiên.\n\n"
        "### §12 Ngưỡng ý nghĩa\n\nAlpha: không áp dụng — nghiên cứu định tính không kiểm định giả thuyết.\n")


def _de_tai_g6(tmp_path: Path, script: str) -> Path:
    d = tmp_path / "S"
    (d / "scripts").mkdir(parents=True)
    (d / "G6_A7_ANALYSIS_SCRIPTS_S.md").write_text("# A7\n", encoding="utf-8", newline="\n")
    (d / "G4_A5_SAP_FINAL_S.md").write_text(_SAP, encoding="utf-8", newline="\n")
    (d / "G6_checkpoint.json").write_text("{}", encoding="utf-8", newline="\n")
    (d / "scripts" / "03_analysis.R").write_text(script, encoding="utf-8", newline="\n")
    return d


def _ket(d: Path) -> dict:
    r = G6Q.evaluate_study("S", out_dir=d, write=False)
    return {k["id"]: k["pass"] for k in r["checks"] if k["id"] in ("G6-AUTO-02", "G6-AUTO-03")}


_MA_HOA = "# Phân tích chủ đề\ncodes <- read.csv('ma_hoa.csv')\ntable(codes$chu_de)\n"


def test_g6_dinh_tinh_khong_ngau_nhien_khong_kiem_dinh_thi_dat(monkeypatch, tmp_path):
    monkeypatch.setattr(G6Q, "_la_dinh_tinh", lambda _d, _s: True)
    assert _ket(_de_tai_g6(tmp_path, _MA_HOA)) == {"G6-AUTO-02": True, "G6-AUTO-03": True}


def test_g6_thiet_ke_dinh_luong_khai_khong_ap_dung_van_can_thong_ke_vien(monkeypatch, tmp_path):
    monkeypatch.setattr(G6Q, "_la_dinh_tinh", lambda _d, _s: False)
    assert _ket(_de_tai_g6(tmp_path, _MA_HOA)) == {"G6-AUTO-02": None, "G6-AUTO-03": None}


@pytest.mark.parametrize("dong", ["idx <- sample(1:20, 5)", "set.seed(1)", "x <- runif(3)",
                                  "import numpy as np\nnp.random.choice([1, 2])"])
def test_g6_dinh_tinh_co_buoc_ngau_nhien_thi_seed_van_can_xac_nhan(monkeypatch, tmp_path, dong):
    monkeypatch.setattr(G6Q, "_la_dinh_tinh", lambda _d, _s: True)
    assert _ket(_de_tai_g6(tmp_path, _MA_HOA + dong + "\n"))["G6-AUTO-02"] is None


@pytest.mark.parametrize("dong", ["chisq.test(tab)", "fit <- glm(y ~ x)", "t.test(a, b)", "res$p.value"])
def test_g6_dinh_tinh_co_kiem_dinh_thi_alpha_van_can_xac_nhan(monkeypatch, tmp_path, dong):
    monkeypatch.setattr(G6Q, "_la_dinh_tinh", lambda _d, _s: True)
    assert _ket(_de_tai_g6(tmp_path, _MA_HOA + dong + "\n"))["G6-AUTO-03"] is None


def test_g6_mau_r_dinh_tinh_cua_he_khong_vuong_hai_mau_chan():
    """Khuôn R định tính mà run_g6_auto sinh phải đi được đường ĐẠT (không có bước ngẫu nhiên / kiểm định)."""
    import run_g6_auto as G6  # noqa: PLC0415

    v = {"exposure": "nhom", "outcome": "chu_de", "time_col": "", "covariates": [], "detection_log": ["test"]}
    r = G6.R_ANALYSIS_MAP_FUNC("qualitative", v, 0, 0.05, 0.80, None, "HR")
    ma = "\n".join(d for d in r.splitlines() if not d.lstrip().startswith("#"))
    assert not G6Q._BUOC_NGAU_NHIEN.search(ma)
    assert not G6Q._KIEM_DINH.search(ma)


# ── B. khoảng hợp lệ cho mọi trường số của 6 kịch bản thêm ─────────────────────────────────────────────────────
_THIET_KE = {"thuan_tap_phoi_nhiem": "cohort", "benh_chung": "case_control", "chan_doan": "diagnostic",
             "mo_hinh_du_bao": "prediction", "tong_quan_gop": "sr_ma", "dinh_tinh": "qualitative"}


def test_moi_truong_so_cua_6_kich_ban_co_khoang_hop_le():
    bs = KBT.bien_so_them()
    assert set(bs) == set(_THIET_KE)
    thieu = [(ma, t) for ma, b in bs.items() for t, _k, _n, _lc, v, lo, hi in b["bo_bien"]
             if v in ("integer", "number") and not (lo and hi and float(lo) < float(hi))]
    assert not thieu, thieu


_G3 = {"p0": 0.3, "prevalence": 0.3, "effect_size": 1.5}


@pytest.mark.parametrize("ma", sorted(_THIET_KE))
def test_du_lieu_mo_phong_nam_trong_khoang_da_khai(ma):
    bs = KBT.bien_so_them()[ma]
    khoang = {t: (float(lo), float(hi)) for t, _k, _n, _lc, v, lo, hi in bs["bo_bien"] if v in ("integer", "number")}
    hang = TV.sinh_du_lieu(_THIET_KE[ma], bs, _G3, 300)
    ngoai = [(t, r[t]) for r in hang for t, (lo, hi) in khoang.items()
             if r.get(t) is not None and not lo <= float(r[t]) <= hi]
    assert not ngoai, ngoai[:5]


@pytest.mark.parametrize("ma", sorted(_THIET_KE))
def test_khoang_da_khai_khong_ep_cat_du_lieu_mo_phong(ma):
    """Bộ sinh ÉP giá trị vào khoảng đã khai — khoảng hẹp hơn dải mô phỏng sẽ âm thầm cắt dữ liệu (dồn ở biên) mà phép
    kiểm «nằm trong khoảng» vẫn xanh. Cùng hạt giống: có khoảng và không khoảng phải ra ĐÚNG cùng dữ liệu."""
    bs = KBT.bien_so_them()[ma]
    tran = {**bs, "bo_bien": [(t, k, n, lc, v, "", "") for t, k, n, lc, v, _lo, _hi in bs["bo_bien"]]}
    assert TV.sinh_du_lieu(_THIET_KE[ma], bs, _G3, 300) == TV.sinh_du_lieu(_THIET_KE[ma], tran, _G3, 300)


# ── G9-T1. tên checklist báo cáo đúng tên hội đồng đòi ─────────────────────────────────────────────────────────
def test_checklist_bao_cao_dung_ten_hoi_dong_g9t1(tmp_path):
    (tmp_path / "G7_A8_MANUSCRIPT_S.md").write_text("# Bản thảo\n\n| 1 | Tiêu đề | Đạt | tr. 1 |\n",
                                                   encoding="utf-8", newline="\n")
    gia = types.SimpleNamespace(out=tmp_path, study="S")
    ten = TV.TronVong._checklist_bao_cao(gia)
    nv = next(x for x in HD.NHIEM_VU["G9"] if x["ma"] == "G9-T1")
    assert ten in {m.replace("<mã>", "S") for m in nv["dau_ra"]}
    assert (tmp_path / ten).is_file()


# ── D. bảng trích xuất cấp nghiên cứu cho tổng quan gộp ────────────────────────────────────────────────────────
def test_hang_so_tep_trich_xuat_trung_hoi_dong():
    assert TV.TEP_TRICH_XUAT_SR == HD.TEP_TRICH_XUAT_SR


def _khoa(d: Path, cot: list, dong: list) -> None:
    (d / "05_clean_locked").mkdir(parents=True)
    with (d / "05_clean_locked" / "x.locked.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cot)
        w.writerows(dong)
    (d / "DATA_LOCK_manifest.json").write_text(json.dumps({"locked_dataset_path": "05_clean_locked/x.locked.csv"}),
                                               encoding="utf-8", newline="\n")


def test_bang_trich_xuat_sr_chi_lay_nghien_cuu_duoc_dua_vao(tmp_path):
    cot = ["study_id", "nam_cong_bo", "tc_rct", "lt_theo_doi_ngan", "n_can_thiep", "bien_co_can_thiep", "n_chung",
           "bien_co_chung", "rob2_tong"]
    _khoa(tmp_path, cot, [["TV001", "2024", "1", "1", "", "", "", "", ""],          # loại: theo dõi ngắn
                          ["TV002", "2019", "1", "0", "6251", "225", "6229", "272", "1"],
                          ["TV003", "2023", "0", "0", "3376", "68", "3395", "66", "3"],  # loại: không phải RCT
                          ["TV004", "2021", "1", "0", "4486", "64", "4508", "86", "2"],
                          ["TV005", "2020", "1", "0", "", "", "", "", ""],            # thiếu số liệu
                          ["TV006", "2018", "1", "1", "5000", "90", "5010", "120", "1"]])  # loại dù đủ số liệu
    gia = types.SimpleNamespace(out=tmp_path, buoc=[])
    TV.TronVong._bang_trich_xuat_sr(gia)
    p = tmp_path / TV.TEP_TRICH_XUAT_SR
    with p.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert [r["study"] for r in rows] == ["TV002", "TV004"]
    assert rows[0] == {"study": "TV002", "year": "2019", "event.e": "225", "n.e": "6251", "event.c": "272",
                       "n.c": "6229", "rob2_tong": "1"}
    assert HD._kiem_bang_trich_xuat(tmp_path, "S") == []
    assert gia.buoc and gia.buoc[-1]["ma"] == 0


def test_bang_trich_xuat_sr_nam_lay_tu_ma_nghien_cuu_khi_khong_co_cot_nam(tmp_path):
    cot = ["study_id", "n_can_thiep", "bien_co_can_thiep", "n_chung", "bien_co_chung"]
    _khoa(tmp_path, cot, [["TN01-2016", "3264", "77", "3217", "110"], ["TN02-2017", "2375", "78", "2419", "120"]])
    gia = types.SimpleNamespace(out=tmp_path, buoc=[])
    TV.TronVong._bang_trich_xuat_sr(gia)
    with (tmp_path / TV.TEP_TRICH_XUAT_SR).open(encoding="utf-8", newline="") as fh:
        assert [r["year"] for r in csv.DictReader(fh)] == ["2016", "2017"]
    assert HD._kiem_bang_trich_xuat(tmp_path, "S") == []


def test_bang_trich_xuat_sr_chua_khoa_thi_khong_ghi(tmp_path):
    gia = types.SimpleNamespace(out=tmp_path, buoc=[])
    TV.TronVong._bang_trich_xuat_sr(gia)
    assert not (tmp_path / TV.TEP_TRICH_XUAT_SR).exists()
    assert gia.buoc[-1]["ma"] is None


def test_buoc_g5_goi_bang_trich_xuat_sau_khi_khoa_cho_tong_quan():
    """Chỗ gọi (dòng THI HÀNH, đọc bằng AST — bình luận cùng chữ không làm xanh): trong `TronVong.g5`, lời gọi
    `self._bang_trich_xuat_sr()` nằm trong nhánh `if self.thiet_ke == "sr_ma"` và đứng SAU lệnh khoá dữ liệu."""
    import ast  # noqa: PLC0415
    import inspect  # noqa: PLC0415
    import textwrap  # noqa: PLC0415

    cay = ast.parse(textwrap.dedent(inspect.getsource(TV.TronVong.g5)))
    dong_khoa = min(n.lineno for n in ast.walk(cay) if isinstance(n, ast.Constant)
                    and n.value == "lock_analysis_dataset.py")
    goi = [n for n in ast.walk(cay) if isinstance(n, ast.If) and "sr_ma" in ast.unparse(n.test)
           and "thiet_ke" in ast.unparse(n.test)
           and any(isinstance(c, ast.Call) and ast.unparse(c.func) == "self._bang_trich_xuat_sr"
                   for b in n.body for c in ast.walk(b))]
    assert goi, "TronVong.g5 không gọi _bang_trich_xuat_sr trong nhánh sr_ma"
    assert all(n.lineno > dong_khoa for n in goi)
